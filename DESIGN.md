# Design

Dark site, colour from the games. Studio pages use Vena's red; each game page uses its
own accent and a background tinted to match.

## Colours (`:root` in assets/css/site.css)

| Token | Value | Notes |
|---|---|---|
| `--signal` | `#ec6a78` | studio accent (Vena's red) |
| `--bg` | `#0b0a0c` | Vena `#130b0f`, What the Buck?! `#08100b`, Fish Don't Return `#060c11` |
| `--raise` | `#151317` | panels, tinted per game |
| `--line` | `#27242a` | dividers, tinted per game |
| `--text` | `#f3f2ee` | |
| `--muted` | `#a4a4aa` | at least 7.9:1 on every background |
| `--accent` | per page | red, What the Buck?! `#84d48c`, Fish Don't Return `#77d9d5` |

Semi-transparent darks are `color-mix` of `--bg` so they pick up the tint. Media corners
18px, buttons rounded 10px, nav chips 8px. Button rows stack full width on phones.

## Type

Big Shoulders Display for headings and the wordmark (weight 800, 700 for large leads), Work Sans
for text (17px, line height 1.6), with its italic for quotes. All OFL, latin subset, in assets/fonts.
The display face has no italic, so `<i>` in a heading is set upright in the accent. Running text
stays under about 75 characters a line.

## Media

The home page shows one game at a time, full screen: a muted gameplay loop of about 8 to 12
seconds, cut from text-free stretches of the game's trailer, over its Steam key art (the
same hero art as its game page), which shows until the loop plays and whenever it can't.
With it come the logo, one line, a store button and a link to the game's page. A switcher
along the bottom names every game with its status and a progress line; it moves on after one
run of the game's loop, pauses while the pointer is on it or something inside has focus,
stops for good once a game is picked, and has a pause button. With reduced motion or data
saving it does not move. Without JavaScript, and on phones, the games stack, one per screen.
A new game is one more slide and one more pick.

Game pages show their 9:16 clips in their own sections. A clip plays while it is in view and
has its own play and pause button; with reduced motion nothing plays by itself. Clip columns
are at most 36svh wide, so a clip and its caption fit on one screen.

At the top of every page the header is see-through over the art, with a soft shade behind
the links; it turns solid as soon as the page scrolls.

## Copy

Short and plain. No em-dashes, no slogans. Buttons in sentence case. German addresses the reader as "du".
The language follows the browser on the first visit and the DE/EN switch after that.
