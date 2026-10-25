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

Game cards are 9:16, three in a row next to the headline and a swipeable row on phones.
Under its line each card gives the game's release status in its accent.
Cards show the first frame of their clip and play it on hover, or for 5 seconds when
scrolled into view on touch screens. Each card has a blurred copy of its poster behind
it. With reduced motion nothing plays by itself. Clip columns are at most 36svh wide, so a
clip and its caption fit on one screen.

## Copy

Short and plain. No em-dashes, no slogans. Buttons in sentence case. German addresses the reader as "du".
The language follows the browser on the first visit and the DE/EN switch after that.
