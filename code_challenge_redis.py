import json
import xml.etree.ElementTree as ET

import redis

class CodeChallengeImplementation:
    """
    Insert the logic for the coding challenge, so that main function in main.py runs without errors.
    """

    # count the processed data bulks. It's not used;
    _processed_bulks=0

    def __init__(self):

        # data member used to save data from past processed messages
        self.cache = {}
        self.r = redis.Redis() 
        self.r.flushdb()  # delete everything at each processing cycle
        self.initiated=False # set to True after first packet is processed
        self.cache_channel_id=[] # cache channel names/identifiers

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
            # save first switch value received in a bulk cycle
            if not self.initiated:
                self.r.set('first_switch',str(switch))
                self.initiated=True

            if switch != None: # save switch only if it's a valid value
                self.r.set('switch',str(switch))

            # store 'average' values and pack them by channel number:
            if average!=None:
                self.r.lpush("channel{}".format(channel), average)
                if channel not in self.cache_channel_id:
                    self.cache_channel_id.append(channel)

            # store categories in the order they come, also, save the channel:
            # skip empty values
            if majority!=None:
                self.r.lpush("majorities", "{},{}".format(channel, majority))



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

    
    def update_majority_winner(self, reverse) -> str:
        """
        Method which traverses the cached messages and returns the current 'majority'
            for the merged data
        """
        current_majority = ""
        current_power=0
        occurences = {} 

        # if the 'reverse' parameter is True, then reverse the working list before processing it:
        working_list = [tuple(x.decode('utf-8').split(',')) for x in self.r.lrange("majorities",0,-1)]
        if not reverse:
            working_list = working_list[::-1]

        '''Process the messages one by one.'''
        for maj in working_list:
            # maj[1] stores the category
            # maj[0] stores the channel
            occurences[maj[0]]=maj[1]
            """
            Process the messages one by one. At each cycle, 
            generate a dictionary that contains the last seen category from each channel
            Store this in 'occurences'
            """

            # fetch the current majority for each channel
            current_majorities = [val[1] for val in occurences.items()]

            possible_winner = self.most_frequent(current_majorities)
            new_power = current_majorities.count(possible_winner)
            old_power = current_majorities.count(current_majority)
            
            #if the new number of majority 'votes' is bigger than the previous one,
            #   consider this new category as current winner:
            if new_power>old_power:
                current_majority=possible_winner
                current_power=new_power

        return current_majority

    def get_averages(self, reverse):
        last_averages=[]

        for channel in self.cache_channel_id:
            if reverse:
                ind=-1
            else:
                ind=0
            working_list = self.r.lrange("channel{}".format(channel),ind,ind)
            last_averages.extend([float(el.decode('utf-8')) for el in working_list])

        return sum(last_averages)/len(last_averages)

    def state(self) -> dict:
        """
        Return the current merged state
        """
        res = {}
        res['switch'] = self.clean_switch(self.r.get('switch').decode('utf-8'))
        res['average'] = self.get_averages(reverse=False)
        res['majority']= self.update_majority_winner(reverse=False)

        return res


    def reversed_state(self) -> dict:
        """ Return the state if the messages were received in the reversed order. """

        res = {}
        res['switch'] = self.clean_switch(self.r.get('first_switch').decode('utf-8'))
        res['average'] = self.get_averages(reverse=True)
        res['majority']= self.update_majority_winner(reverse=True)

        return res