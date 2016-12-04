# P3: Wrangle OpenStreetMap Data - OpenStreetMap Project

## Map Area
Newbury, Berkshire, United Kingdom

I decided to use a custom bounding box as there was not a metro export available for my hometown. The bounding box I used was:
- http://www.openstreetmap.org/export#map=10/51.2671/-0.8123
- min Longitude: -1.6658
- min Latitude: 51.2881
- max Longitude: -0.9462
- max Latitude: 51.5702

The area I chose contained the area surrounding my hometown. I am a keen cyclyst that uses the OpenStreetMap data to not only plan my cycling routes before a ride but also use them for mapping on my Garmin cycling computer while out on a ride. Having the opportunity to improve the local mapping would not only benefit the community but also my route planning and navigation at the same time.

## Problems Encountered in the Map

Having downloaded a sufficient data set to cover the area around Newbury



## Sort cities by count, descending

```sql
SELECT tags.value, COUNT(*) as count 
FROM (SELECT * FROM node_tags UNION ALL 
      SELECT * FROM way_tags) tags
WHERE tags.key LIKE '%city'
GROUP BY tags.value
ORDER BY count DESC;
```
Within the OSM extract there were 98 different city tag values present. I have included the top 10 results which have been edited for readability:
```sql
value  count
Reading     3285
Newbury     274
Basingstoke 121
Tadley      16
4           11
Shrivenham  10
Wantage     9
6           7
10          6
Didcot      6
```
The above results show the most common city value to be used is Reading, this would be in line with expections as it is the largest town in the areas and encompasses the eastern portion of the bounding box I selected. The second most common value is Newbury which is my hometown but proportionally it is much smaller than Reading so I would expect nothing less than the count of value to be much smaller.
