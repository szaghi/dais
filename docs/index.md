---
layout: home

hero:
  name: DAIS
  text: Desktop Assignable Input Switch
  tagline: A one-key MX macropad -- a raised platform for a single key, standard or artisan. RP2040 board, upstream QMK firmware, and a parametric case generated in Python with build123d.
  image:
    src: /photo/split-trapezoid/hero.webp
    alt: Split case, trapezoidal plan
  actions:
    - theme: brand
      text: Quick start
      link: /guide/quick-start
    - theme: alt
      text: The four designs
      link: /designs/
    - theme: alt
      text: Printing
      link: /guide/printing

features:
  - icon: ⌨️
    title: A miniature keyboard
    details: A 7 deg typing wedge, the key sunk in a 1U well inside wide bezels, crisp chamfered edge breaks -- the vocabulary of a top-mount custom keyboard, scaled to one switch.
    link: /guide/
    linkText: Design language
  - icon: 🧩
    title: Four designs, one code base
    details: Two one-piece wedges sculpted by a ball-cutter cove, and a split case -- rectangular or trapezoidal -- whose seam is the only feature. Every design exports a complete, self-contained part set.
    link: /designs/
    linkText: Compare them
  - icon: 📐
    title: Fully parametric
    details: Every look and fit dimension is one constant. Change the board, the switch drop or the bezel and the whole case resizes around it.
    link: /guide/parameters
    linkText: Parameters
  - icon: 🖨️
    title: Prints without supports
    details: Top shells print top face down; every internal feature grows from the top skin. The test suite checks for overhangs, clashes and plate clearance on every build.
    link: /guide/printing
    linkText: Printing
  - icon: 🔌
    title: Upstream QMK
    details: No custom keyboard definition -- the upstream handwired/onekey target with a one-line keymap and bootmagic, so the closed case can still be flashed.
    link: /guide/firmware
    linkText: Firmware
---
