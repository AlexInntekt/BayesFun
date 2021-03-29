import json
import xml.etree.ElementTree as ET

class CodeChallengeImplementation:
    """
    Insert the logic for the coding challenge, so that main function in main.py runs without errors.
    """

    # count the processed data bulks. It's not used;
    _processed_bulks=0

    def __init__(self):

        # data member used to save data from past processed messages
        self.cache = {} 

        self.initiated = False # to mark the processing of first data packet

        # initiate main pairs
        self.cache['channels'] = {} # store values for average

        self.cache["majorities"] = {} # store current majority for each channel
        self.cache["forward_maj_winner"] = () # for state value
        self.cache["backwards_maj_winner"] = () # for reversed state value


        # that's for my fun:  :)
        CodeChallengeImplementation._processed_bulks+=1
        globals()['no_processed_bulks'] = CodeChallengeImplementation._processed_bulks


    def clean_switch(self, value):
        """
        Procedure that cleanse the switch field.
            Converts in the following manner:
            - strings 'false' and 'False' to bool False
            - strings 'true' and 'True' to bool True
            - boolean type stays boolean
            - None to None
            - 0 to False for the C convention
            - any non-zero number to True
            - anything else to True
        """

        if type(value)==bool:
            return value
        elif type(value)==str:
            if value=='true' or value=='True':
                return True
            elif value=='false' or value=='False':
                return False
        elif value==0:  # trying to adapt to c++ convention too
            return False
        elif value==None: # None will allow the merger to skip this value
            return None

        return bool(value) # last attempt to return a boolean

    
    def clean_average(self, value):
        '''
        The 'average' value will be set to None and skiped 
            if it can't be converted to a number
        '''   

        try:
            value = float(value)
        except ValueError:
            value = None

        return value

    def clean_majority(self,value):
        '''
        Method that cleanses the majority field.
        Makes sure the validated field is always None or a string.
        '''
        if value==None or value=="":
            return None
        else:
            return str(value)

    def clean_channel(self,value):
        '''
        Method that cleanses the channel field.
        Makes sure the validated field is always None or a string.
        '''
        if value==None or value=="":
            return None
        else:
            return str(value)


    def extract_data_from_content(self, content) -> tuple:
        """
            Method that extracts the values switch, channel, average and majority
        from the file content.
            The content can be JSON or XML.
            The first character from the content is used to guess if it's JSON or XML.
        """

        content = content.lower() # the data is independent of case, convert it to lowercase to avoid problem 
        # in JSON parsing because of the wrong boolean values

        # use the first character from the data, to check if the content is JSON or XML
        first_char = content[0]
        if first_char != '<':
            data = json.loads(content)
            switch = self.clean_switch(data['switch'])
            channel = self.clean_channel(data['channel'])
            average = self.clean_average(data['average'])
            majority = self.clean_majority(data['majority'])
        else:
            root = ET.fromstring(content)
            for child in root:
                
                if 'switch'==child.tag:
                    switch = self.clean_switch(child.text)
                if 'channel'==child.tag:
                    channel = self.clean_channel(child.text)
                if 'average'==child.tag:
                    average = self.clean_average(child.text)
                if 'majority'==child.tag:
                    majority = self.clean_majority(child.text)

        return (switch, channel, average, majority)


    def merge(self, content) -> None:
        """
        Method that merges a new message in the cached centralized data
        """
        switch, channel, average, majority = self.extract_data_from_content(content)
        
        # Packets with empty 'channel' are skipped altogether, because they can't be mapped anywhere:
        if channel!='':

            if switch != None: # save switch only if it's a valid value
                self.cache['last_switch'] = switch

            # initiate the channel node if it does not exist:  
            if channel not in self.cache['channels']:
                self.cache['channels'][channel] = []

            # store 'average' values and pack them by channel number. Save only last and first.
            if average!=None:
                saved_averages = len(self.cache['channels'][channel])
                if saved_averages==0 or saved_averages==1:
                    # if this is the first or second packet, then just add the average to the list
                    self.cache['channels'][channel].append(average)
                else:
                    # if this is a data packet after the first two, override the last 'average' field to constant memory consumption:
                    self.cache['channels'][channel][1] = average

            # save current majority for the channel in the data packet:
            self.cache["majorities"][channel] = majority
            
            # take all current majorities and find the most frequent one and its frequency:
            current_majorities = [val for key, val in self.cache["majorities"].items()]
            most_frequent_maj = self.most_frequent(current_majorities)
            count_most_frequent_maj = current_majorities.count(most_frequent_maj)
            current_maj = (most_frequent_maj, count_most_frequent_maj)

            #  if this is the first data packet that is processed, initiate the fields in the cache structure:
            if self.initiated==False:
                self.cache['first_switch'] = switch
                self.cache["forward_maj_winner"] = current_maj
                self.cache["backwards_maj_winner"] = current_maj
                self.initiated=True
            else:
                # this is the frequency of the previous majority winner:
                old_votes = current_majorities.count(self.cache["forward_maj_winner"][1])

                # update 'majority' value for backward and forward processing:
                if self.cache["forward_maj_winner"][1]<count_most_frequent_maj or old_votes<count_most_frequent_maj:
                    self.cache["forward_maj_winner"] = current_maj

                if self.cache["backwards_maj_winner"][1]<count_most_frequent_maj:
                    self.cache["backwards_maj_winner"] = current_maj




    def most_frequent(self, elements):
        """
        Method which finds the most frequent element in a list
        """   
        counter = 0
        current_most_freq = elements[0]
          
        for el in elements:
            freq = elements.count(el)
            if(freq > counter):
                counter = freq
                current_most_freq = el
      
        return current_most_freq



    def state(self) -> dict:
        """
        Return the current merged state
        """
        res = {}
        res['switch'] = self.cache['last_switch']
        averages = [float(val[-1]) for key,val in self.cache['channels'].items()]
        res['average'] = sum(averages)/len(averages)
        res['majority']= str(self.cache["forward_maj_winner"][0])

        return res


    def reversed_state(self) -> dict:
        """ Return the state if the messages were received in the reversed order. """

        res = {}
        res['switch'] = self.cache['first_switch']
        averages = [float(val[0]) for key,val in self.cache['channels'].items()]
        res['average'] = sum(averages)/len(averages)

        res['majority']= str(self.cache["backwards_maj_winner"][0])
        # print(self.cache)
        # print()
        return res