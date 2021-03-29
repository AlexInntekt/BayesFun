# Solution design - dictionary approach

## Strategy - dictionary approach

I cache the processed data into a dictionary (_cache_). 

For a large data set or concurent access needs, this in-memory dictionary can be replaced with a non-relational DB.


The _cache_ contains:   
- the first and last switch values retrieved.
- _channel_ which nests the lists with _average_ values
- _majorities_ which contains tuples of channels and majorities
in the order they arrive
- _majority_power_ which is the number of 'votes' of current 'majority'
- _majority_ which will store the current majority after the method _update_majority_winner_ is executed.

The methods state() and reverse_state() call _update_majority_winner_ which traverses the cached data in order to generate the 'majority'.


## Strategy - Pandas

I cache the raw data into a pandas dataframe. 
The same strucuture is preserved. 

Two additional methods get_averages() and get_switch()
are used to generate the values from the dataframe.

The methods state() and reverse_state() call _update_majority_winner_ which traverses the cached data in order to generate the 'majority'.



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





