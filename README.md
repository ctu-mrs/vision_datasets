
## Public datasets for research  on multi-domain object detection
The current datasets have been collected during the preparation phase of the Subt DARPA comptetition.


## Dataset download:
The dataset is accessible via a public [link](http://ptak.felk.cvut.cz/personal/stasiyur/darpa_system_dataset/dataset.zip) - beware, the datset is 201 GB, so it will take some time to download it.


##  Format
The dataset was done using labelme tool. To convert it to COCO format, you can use the modified labelme2coco package, which adjusts the mistakes in the labeling names.

## Split
To split the dataset into parts, we have used ``cocosplit`` package. The modified version of the package is included in the repository.
