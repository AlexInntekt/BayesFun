# Solution design - dictionary approach

## How to run
In order to run an approach, rename one of the `code_challenge_{approach}.py` file and run main.py.

## Dependencies  
redis-server installed with    
Linux: `sudo apt-get install redis-server`    
MacOS: `brew install redis`    
PIP:       
redis==3.5.3   
pandas==1.1.4      
   

## Strategy - dictionary approach

I cache the processed data into a dictionary (_cache_). 

For a large data set or concurent access needs, this in-memory dictionary can be replaced with a non-relational DB or a message broker can be added for distributed access (like Redis or ZeroMQ).


This is an improved version of the dictionary approach.    
Instead of saving in RAM memory the lists with averages, only first and last values are saved.     
Also, instead of creating an in-memory list with *all* 'majority' values from all packets, I added an algorithm that computes the 'majority' field for both forward and backward processing on the spot, avoiding huge memory consumption this way.

No mather how many data packets the merger receives, the memory consumption stays the same.
This is an example of state of the cached data:

```
{'channels': {'2': [85.0, 59.0], '1': [56.0, 24.0], '3': [86.0, 58.0]}, 'majorities': {'2': 'foo', '1': 'foo', '3': '1000'}, 'forward_maj_winner': ('foo', 2), 'backwards_maj_winner': ('bar', 2), 'last_switch': True, 'first_switch': True}
```

`cache['channels']` contains the 'average' values, the first and last one.
`cache['last_switch']` and `cache['first_switch']` contains the first and last switch values.
`cache["forward_maj_winner"]` and `cache["backwards_maj_winner"]` contain the 'majority' value for the merged data, which is computed on the spot at each processing.
`cache["majorities"]` contains a dictionary with the state of current majorities for each channel.



## Strategy - Pandas approach

I cache the raw data into a pandas dataframe. 
The same strucuture is preserved. 

Two additional methods get_averages() and get_switch()
are used to generate the values from the dataframe.

The methods state() and reverse_state() call _update_majority_winner_ which traverses the cached data in order to generate the 'majority'.


## Strategy - Redis approach

I save the data with Redis.   
The structure is as follows:  
`KEYS *`

1) "channel3"  
2) "channel1"  
3) "channel2"  
4) "channel4"   
5) "first_switch"  
6) "majorities"  
7) "switch"  

The `switch` and `first_switch` saves the first and last values of the switch field.
In the `channel` lists the average values are stored in the order the packets are processed.
The `majorities` field stores the majority categories in order.

A list with all the channel names are saved in memory. An additional list could be saved in Redis, but I chose to save it in the merger class' memory as an optimization measure to avoid additional querries (0.01s gain in total)

The methods state() and reverse_state() call _update_majority_winner_ which traverses the cached data in order to generate the 'majority' value.




## Fields validation

These validation methods are called before the merging process occurs.

All of them set the fields to None in case the raw value is not valid or there is an empty string. 

A field with None value will be skipped during merging.
Other validation operations are applied depending on the field.


### _clean_switch()_
Applies a conversion in the following manner:  
- strings 'false' and 'False' to boolean False
- strings 'true' and 'True' to boolean True
- None to None
- 0 to False
- any non-zero number to True
- anything else to True

### _clean_average()_
 the 'average' field is cleaned with _process_average()_:
If the value can't be converted to a number, then None is returned, so that the merger process can know that it has to skip this value.

### _clean_majority()_
It makes sure majority is non-empty. It returns None or a string value.

### _clean_channel()_
Converts empty string values to None so that the merger can know it should skip the whole data packet because it can't map the other values to a channel source.





