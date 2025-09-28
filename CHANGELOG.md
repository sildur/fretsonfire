# CHANGELOG

<!-- version list -->

## v1.4.6 (2025-09-28)

### Bug Fixes

- **ci**: Conditionally upload distribution artifacts based on release status
  ([`22770c6`](https://github.com/sildur/fretsonfire/commit/22770c604b6f7f3a75f89e852cb2069db75b7abb))

### Documentation

- Merge legacy changelog into markdown
  ([`e7f8065`](https://github.com/sildur/fretsonfire/commit/e7f806545e1de4d472a5e51c0a47d1d38c3a4b52))


## v1.4.5 (2025-09-28)

### Bug Fixes

- **translations**: Make update script Python 3 compatible
  ([`6d305df`](https://github.com/sildur/fretsonfire/commit/6d305df8e8bbaacf995d775e17e6b277f1b2e49a))

### Build System

- **ci**: Fix PSR config
  ([`ccced37`](https://github.com/sildur/fretsonfire/commit/ccced37a3e113012b8ff4002bb7ed52264edcce8))


## v1.4.4 (2025-09-28)

### Bug Fixes

- Change Python shebang to use env for Python 3
  ([`5258d81`](https://github.com/sildur/fretsonfire/commit/5258d819d812e5af4365cd4307bd9b9fe4c15734))


## v1.4.3 (2025-09-28)

### Bug Fixes

- Replace os.system with subprocess for svg2png
  ([`9122aea`](https://github.com/sildur/fretsonfire/commit/9122aeae56f6abde3bf0c5fe627864baced5ebc4))


## v1.4.2 (2025-09-28)

### Bug Fixes

- **config**: Parse upload URL host safely
  ([`4f3f109`](https://github.com/sildur/fretsonfire/commit/4f3f10944c231d5739f8df20038cba3b8af675f6))

### Build System

- **ci**: Enable manual release runs and full semantic-release build
  ([`5eb56ab`](https://github.com/sildur/fretsonfire/commit/5eb56abc9feb8a5af5aa36a181e2d11e9372e1ef))

- **ci**: Fix build command
  ([`809c2d2`](https://github.com/sildur/fretsonfire/commit/809c2d267f4817a4f274a6512d3b3d9f83e5bead))


## v1.4.1 (2025-09-28)

### Bug Fixes

- Drop accidental highscores from songs.ini
  ([`1e2e65a`](https://github.com/sildur/fretsonfire/commit/1e2e65ab63e31b97c8462e9082cbe8b86369607f))

- **gameplay**: Keep pause menu from ending song early
  ([`2cef1ca`](https://github.com/sildur/fretsonfire/commit/2cef1ca2c5360c35a07a39557c98dd2f7860cb81))

### Build System

- Repair distributable targets
  ([`72e7e06`](https://github.com/sildur/fretsonfire/commit/72e7e0638a26b120103d44900a7d1a390eff5c04))

- **ci**: Add semantic-release workflow and config
  ([`957e31b`](https://github.com/sildur/fretsonfire/commit/957e31bdb2d8fc927d5305841320d6302ab4fc46))

- **ci**: Fix branch name in github action
  ([`5185069`](https://github.com/sildur/fretsonfire/commit/51850696b82873befc720b3b234cbe5223a70afc))

### Chores

- Add dependabot configuration
  ([`246ff99`](https://github.com/sildur/fretsonfire/commit/246ff9906e84beaa76dec66b7f2ba7894b387609))

### Refactoring

- **audio**: Drop unused pyglet backend
  ([`217d1bb`](https://github.com/sildur/fretsonfire/commit/217d1bbcab6b8fc962cf45251940956966dea65d))


## v1.4.0 (2025-09-27)
- Repackaged project with pyproject.toml + setuptools build hooks.
- Moved game assets under src/fretsonfire/data for wheel installs.
- Added automatic gettext compilation during builds.
- Declared dependencies for async networking and runtime assets.

## v1.3.110
* Wrote concise instructions for building and installing the game.
* Removed runtime SVG support. All images must be pre-rasterized as PNG graphics now. This also removes the dependency on Amanith, making the game simpler to build and package.
* Reworked the build system. Now an installation package can be created with a single command for Windows and Mac OS X.
* Added textured fretboard strings and bars.
* Updated the translations.

## v1.2.512
* Effects optimization
* Font rendering optimization
* Miscellaneous bug fixes
* Added import support for Guitar Hero 80s
* Translation updates
* World Charts standing is now reported after each game

## v1.2.451
* Fixed some bugs with the tapping implementation
* Audio performance and stability fixes
* Song chooser filter enhanced
* Introduced new World Charts
* Linux packaging fixes

## v1.2.438
* Added custom fretboard and background support
* Volume control
* Song folder support
* Fixed screw-up volume
* Align notes to beat lines again
* Fixed missing encoding error on linux
* Dual core performance improvements
* Fixed crash with strangely named joysticks
* Fixed backspace etc. on mac
* Delete rhythm file after importing each song
* Improved importer encoding quality
* Made notes disappear when they are hit
* Fixed volume saturation issue with GH2 tracks
* Fixed performance issue with note effect
* Move the multiplier text upwards
* Pause the song while the menu is shown
* Implement playing multiple streaming OGG files simultaneously
* Fixed the timer skew and add a high priority mode
* Fixed the priority of the loading screens to improve loading time
* Made the fret color configurable with the theme
* Hit counter
* Type-ahead find for song chooser
* Fix Numeric memory leak
* Fix importing two missing songs on GH1 and GH2 disks
* Tapping support, aka hammer-ons and pull-ofs
* PPC Mac fixes

## v1.1.324
* Support for importing Guitar Hero(TM) II songs
* Support for game modifications
* Widescreen support
* Added the submitted translations to the game. Thanks to everyone who sent theirs in!
* Many bugfixes related to configuration settings, song creation, etc.
* Mac OS X fixes

## v1.0.263

* Mac OS X support. Okay, it's experimental, but it's there. Many thanks to Tero Pihlajakoski for his work on the Mac
  package!
* Windows installer
* Localization support
* Improvements to the song editor
* Fixed a major memory leak
* Lefty mode
* Support for cassette labels and colors
* General performance tuning

## v1.0.225

* Added a Guitar Hero(tm) song importer.
* Fixed the key-release bug for long notes introduced by the previous version.
* Added support for joystick axes and hats.
* Added adjustable song delay in the editor.
* Improved song chooser to remember last played song.
* SDL_mixer and SDL_ttf added to Linux package to ease running on e.g. FreeBSD.
* Added custom color scheme support.
* Score multiplier now resets when notes are missed.
* Added new difficulty level and support for songs with varying tempo.

## v1.0.192

* Added joystick support.
* Added support for two different pick keys.
* Only show the available difficulty levels for songs.
* Fixed the startup problems on video cards that do not support antialiasing.
* Fixed the red screen of death.
* Added the missing DLL to the Window version.
