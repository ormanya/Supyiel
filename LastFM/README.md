LastFM for Supybot/Limnoria
==============

A Supybot/Limnoria plugin for LastFM, forked from [Glolol/Supyplugins](https://github.com/GLolol/SupyPlugins/LastFM).

### Changes made in this fork

- Code cleanup, formatting enhancements, and various bugfixes.
- DB implementation to track nicks rather than hostmasks, for better support of networks that change hostmask with user class progression
- added sa (similar artists), compare, and wp (what's playing) plugins
- added non-printable character to nicks printed to channel, to avoid highlighting

### Setup and Usage

Before using any parts of this plugin, you must register on the LastFM website and obtain an API key for your bot: http://www.last.fm/api/account/create

After doing so, you must then configure your bot to use your key: `/msg <botname> config plugins.LastFM.apiKey <your-api-key>`.

Showing now playing information:
```
<@ormanyal> %np RJ
<@myBot> RJ listened to Apache by The Shadows [Back To Back] at 01:42 PM, October 10, 2015
```

Showing profile information:
```
<@ormanya> %profile RJ
<@myBot> RJ (realname: Richard Jones) registered on 03:50 AM, November 20, 2002; age: 0 / m; Country: United Kingdom; Tracks played: 114896
```
