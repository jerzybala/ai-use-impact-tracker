**<span class="underline">AI and Work Tracker</span>**

**Data Preparation and computation rules**

**Data source:** For the Global Mind we primarily use only Google
Display and Meta data. Data from Google Search is excluded and organic
traffic is down-weighted to 10%. We need to decide what to use for the
tracker.

**Data cleaning**: We should use our standard cleaning criteria

**Demographic-Country averages**: For Global Mind we first compute the
average for each age-sex group within each country (e.g. 18-24-M-USA)
and then average in steps as follows:

1)  Age average = average of M and F groups for that age group

2)  Country average = weighted average based on UN age distribution in
    the country (e.g. African countries skew younger with an average age
    of 18 whereas European countries skew older with an average age in
    the 40s).

3)  Regional average = population weighted average of countries in the
    region.

4)  For any time range we pool all the data in that time range (so if we
    are calculating a monthly average we will pool all data in that
    month and if we are calculating for the quarter we pool all data for
    the quarter).

**Analysis** (I think these three views would be sufficient to start
with – we can get more fancy in the future if necessary but I think this
is really what people want to know).

1)  Questions of focus: Here are the questions/fields that we should
    include. I have also provided a suggested weighting for an index.

|                                                         | AI index weighting |
| ------------------------------------------------------- | ------------------ |
| ai\_impact\_work\_caused\_me\_to\_lose\_my\_job         | \-1                |
| ai\_impact\_work\_created\_new\_job\_opportunities      | 1                  |
| ai\_impact\_work\_improved\_my\_work\_quality           | 0.5                |
| ai\_impact\_work\_increased\_pressure\_to\_work\_faster | \-0.5              |
| ai\_impact\_work\_made\_it\_harder\_to\_find\_work      | \-0.75             |
| ai\_impact\_work\_no\_impact                            | 0                  |
| ai\_impact\_work\_not\_sure                             | 0                  |
| ai\_impact\_work\_worry\_about\_future\_my\_job         | \-0.25             |

2)  Trend views

<!-- end list -->

1)  Global and Regional trends by month for the index as well as select
    elements such as job loss.

2)  Trends by quarter for select countries where we have larger data.

3)  Trends by quarter (or month if data is sufficient) by age group or
    gender group. (e.g. Global males or Global 18-24)

<!-- end list -->

3)  Map views

For a selected demographic (e.g. age group or gender group) and time
period (last year, year to date, last quarter) show select items such as
the AI impact index and AI job loss % on a world map.

4)  Country Ranking graphs

Show horizontal bar graph rankings of countries by AI impact index
and/or job loss %
