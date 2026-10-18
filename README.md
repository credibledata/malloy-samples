# Malloy Analysis Examples (and datasets)

This repository contains example data analysis and common patterns for expressed in Malloy.  Each of the examples can be run from Notebooks.  The 'patterns' are designed to be small and simple and show off how to acomplish some task.  The examples are designed to show how to setup a more.

If you are reading this on Github, you can run these examples directly from your web browser. 

* Make sure you are logged into Github
* press '.' (the period key)
* Install the Malloy Extension

## Getting Started
  * [Hello World Example](names/names1.malloy) - A very simple example with a single table shows how to query data in Malloy

## Data Analysis Patterns
  * [Comparing Timeframes](patterns/yoy.malloy) - There are several different ways of doing timeframe comparisons.  
  * [Foreign Sums](patterns/foreign_sums.malloy) - Malloy can aggregate safely anywhere in a network of joins.  Example explains the different patterns.
  * [Reading Nested Data](patterns/reading_nested.malloy) - JSON, Parquet, Protobuff, log data is often a graph, not a table.  Malloy can naturally read and aggregate from anywhere in this graph.
  * [Percent of Total](patterns/percent_of_total.malloy) - Malloy provides 'level of detal' calculations that, among other things makes calculating percent of total easy at any level of heirachy.
  * [Cohort Analysis](patterns/cohorts.malloy) - It is often useful to see how groups of people behave over time.
  * [Nested Subtotals](patterns/nested_subtotals.malloy) - With a single table we can only look at one or two perspectives at a time.  With nesting, this is unlimited.
  * [Other - Creating an Other Bucket](patterns/other.malloy) - Looking at several groups and combining the rest into 'Other'.
  * [Auto-bining Historgrams](patterns/autobin.malloy) - In many tools, you need to fix the axis for histograms.  In malloy we can dynamically figure out the approiate bucketing for the data.
  * [Moving Average](patterns/moving_avg.malloy) - Moving averages can give a better idea of trends.
  * [Data from JSON API](patterns/apijson.malloy) - We can use a JSON API endpoint as a data source. 
  * [Sessionize/Map Reduce](patterns/sessionize.malloy) - A common data pattern is to read events and combine them into session.
  * [Dimensional Indexes](patterns/dim_index.malloy) - Malloy can find the most common values in your dataset.
  * [Arrays - Unnesting Data](patterns/unnest_data.malloy) - Some functions return arrays.  How to work with them in Malloy. 

## Examples

  * [Auto Recalls](auto_recalls/README.malloy)
  * [E-Commerce Example](ecommerce/README.malloy)
  * [FAA Flight Data Example](faa/README.malloy)
  * [IMDB](imdb/README.malloy)


## [Google BigQuery](bigquery)

These examples require a [Google Cloud](https://cloud.google.com) login.

## Additional Resources:

* [Homepage](http://www.malloydata.dev)
* [Docs and Guides](https://malloydata.github.io/documentation/)
* [Malloy Github repository](https://github.com/malloydata/malloy/)
* Join our [Slack community](https://malloydata.github.io/slack)
