# Club fair poster

Print-ready sheets for the Hackley Improv Club club-fair posterboard
(22 x 28 in board used landscape, wings folded 18 cm in from each side).

- `club-fair-poster.pdf` - 6 letter-size pages, one mounting sheet each, with
  bleed, corner trim marks, and a "Sheet N" label outside the trim.
- `assembly-guide.pdf` - one-page board diagram with every measurement and
  the mounting steps.
- `board-preview.png` - what the finished board looks like.

Print at 100% / "Actual size" (not "fit to page"), then cut on the marks.

To regenerate after editing `make_poster.py`:

    pip install reportlab qrcode pillow
    python3 make_poster.py

`fonts/` holds Poppins and Playfair Display (SIL Open Font License, see
`fonts/OFL.txt`). `assets/` holds the club logo pulled
from the Improv Club QR-code PDF, plus the club hero image from Hackley Clubz. The QR code is regenerated as vector art
from the sign-up URL inside the script.
