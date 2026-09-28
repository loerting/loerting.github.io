# Design

Dark site, colour from the games. Studio pages use one yellow; each game page uses its
own accent and a background tinted to match.

## Colours (`:root` in assets/css/site.css)

| Token | Value | Notes |
|---|---|---|
| `--signal` | `#ffd23f` | studio yellow |
| `--bg` | `#0b0a0c` | Vena `#130b0f`, Fish Don't Return `#060c11` |
| `--raise` | `#151317` | panels, tinted per game |
| `--line` | `#27242a` | dividers, tinted per game |
| `--text` | `#f3f2ee` | |
| `--muted` | `#a4a4aa` | at least 7.9:1 on every background |
| `--accent` | per page | yellow, Vena `#ec6a78`, Fish Don't Return `#77d9d5` |

Semi-transparent darks are `color-mix` of `--bg` so they pick up the tint. Media corners
18px, buttons fully round.

## Type

Bricolage Grotesque for headings and the wordmark (width 75-80, weight 700-800), Geist
for text (17px, line height 1.6). Both OFL, latin subset, in assets/fonts.

## Media

Cards show the first frame of their clip and play it on hover, or for 5 seconds when
scrolled into view on touch screens. Each card has a blurred copy of its poster behind
it. With reduced motion nothing plays by itself.

## Copy

Short and plain. No em-dashes, no slogans. Buttons in sentence case.
