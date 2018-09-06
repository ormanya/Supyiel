LastFM for Supybot/Limnoria
==============

A Supybot/Limnoria plugin for LastFM, forked from [Glolol/Supyplugins](https://github.com/GLolol/SupyPlugins/LastFM).

### Changes made in this fork

- Code cleanup, formatting enhancements, and various bugfixes.
- DB implementation to track nicks rather than hostmasks, for better support of networks that change hostmask with user class progression
- added sa (similar artists), compare, and wp (what's playing) plugins
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
