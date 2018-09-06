LastFM for Supybot/Limnoria
==============

A Supybot/Limnoria plugin for LastFM, forked from [Glolol/Supyplugins](https://github.com/GLolol/SupyPlugins/LastFM).

### Changes made in this fork

- code cleanup, formatting enhancements, and various bugfixes.
- DB implementation to track nicks rather than hostmasks, for better support of networks that change hostmask with user class progression
- added bio, sa (similar artists), compare, whatspplaying, and unset commands
- added non-printable character to nicks printed to channel, to avoid highlighting
- added YouTube links to now playing responses

### Setup and Usage

Before using any parts of this plugin, you must register on the LastFM website and obtain an API key for your bot: http://www.last.fm/api/account/create

After doing so, you must then configure your bot to use your key: `/msg <botname> config plugins.LastFM.apiKey <your-api-key>`.

Showing now playing information:
```
<@ormanya> .np RJ
<@myBot> RJ is listening to Restless (Extended Mix) by New Order [Complete Music] [16/3652] https://www.youtube.com/watch?v=01TOWTBKSho
```

Showing profile information:
```
<@ormanya> .profile RJ
<@myBot> RJ registered on 09:35 PM, July 27, 2006; Country: Canada; Artists played: 1659 Tracks played: 41207 URL: https://www.last.fm/user/RJ
```
All commands:
- bio <artist> - Returns biography for the artist
- compare \<user\> [\<user2\>] - Reports the percent similarity between two users, based on their top 100 artists over the last 12 months  
- np [\<user\>] -- Announces the track currently being played by <user>. If <user> is not given, defaults to the LastFM user configured for your current nick
- profile [\<user\>] - Prints the profile info for the specified LastFM user. If <user> is not given, defaults to the LastFM user configured for your current nick. 
- sa \<artist\> - Lists other similar artists. 
- set <user> - Sets the LastFM username for the caller and saves it in a database.
- topartists [\<user\>] [\<period\>] - Reports the top 10 artists for the user, over the specified period. Options for <period> are "overall | 7day | 1month | 3month | 6month | 12month". Default period is 1month. 
- unset \<user\> - Removes a user from the LastFM database. 
- whatsplaying  - Announces the track currrently being played by all users in the channel. 
