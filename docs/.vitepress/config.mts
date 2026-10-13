import { withMermaid } from 'vitepress-plugin-mermaid'

// one sidebar, in reading order: prev/next links walk the whole documentation
const docs = [
  {
    text: 'Start here',
    items: [
      { text: 'About',       link: '/guide/' },
      { text: 'Quick start', link: '/guide/quick-start' },
      { text: 'Status',      link: '/guide/status' },
    ],
  },
  {
    text: 'Designs',
    items: [
      { text: 'Overview',                     link: '/designs/' },
      { text: 'Side coves',                   link: '/designs/side-cove' },
      { text: 'Wrap cove',                    link: '/designs/wrap-cove' },
      { text: 'Split case',                   link: '/designs/split' },
      { text: 'Split case, trapezoidal plan', link: '/designs/split-trapezoid' },
      { text: 'Options and patterns',         link: '/designs/options' },
    ],
  },
  {
    text: 'Build it',
    items: [
      { text: 'Printing',  link: '/guide/printing' },
      { text: 'Assembly',  link: '/guide/assembly' },
      { text: 'Firmware',  link: '/guide/firmware' },
    ],
  },
  {
    text: 'Reference',
    items: [
      { text: 'Parameters',   link: '/guide/parameters' },
      { text: 'Architecture', link: '/guide/architecture' },
      { text: 'Development',  link: '/guide/development' },
    ],
  },
]

export default withMermaid({
  title: 'DAIS',
  description: 'DAIS, Desktop Assignable Input Switch: a one-key MX macropad with a parametric build123d case, RP2040 and QMK',
  base: '/dais/',
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/dais/icon.svg' }],
  ],

  themeConfig: {
    logo: '/icon.svg',
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Start here', link: '/guide/', activeMatch: '^/guide/(index|quick-start|status)?$' },
      { text: 'Designs', link: '/designs/', activeMatch: '^/designs/' },
      { text: 'Build it', link: '/guide/printing', activeMatch: '^/guide/(printing|assembly|firmware)' },
      { text: 'Reference', link: '/guide/parameters', activeMatch: '^/guide/(parameters|architecture|development)' },
    ],

    sidebar: {
      '/guide/': docs,
      '/designs/': docs,
    },

    search: {
      provider: 'local',
    },

    outline: [2, 3],

    footer: {
      message: 'Released under the <a href="https://github.com/szaghi/dais/blob/main/LICENSE">MIT License</a>. Case geometry generated with <a href="https://build123d.readthedocs.io">build123d</a>; firmware: <a href="https://qmk.fm">QMK</a>.',
      copyright: 'Copyright © 2026 Stefano Zaghi',
    },
  },

  mermaid: {},

  vite: {
    // mermaid >= 11.16 ships es2022 syntax; VitePress's default es2020 target makes esbuild
    // reject its chunks. es2022 needs no lowering and is within the browser floor. Both
    // settings are needed: build.target covers `vitepress build`, optimizeDeps covers the
    // dependency pre-bundling of `vitepress dev`.
    build: {
      target: 'es2022',
    },
    optimizeDeps: {
      esbuildOptions: { target: 'es2022' },
      // vitepress-plugin-mermaid pre-bundles a fixed list of mermaid's CommonJS deps; mermaid
      // >= 11.17 adds fastdom, which served raw breaks the dev page (white screen, "does not
      // provide an export named 'default'"). Pre-bundling mermaid itself folds in every dep,
      // whatever mermaid adds next. The plugin appends its own list to this one.
      include: ['mermaid'],
    },
  },
})
