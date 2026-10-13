// DAIS docs theme: the default VitePress theme, the DAIS palette, and <Views> for drawing galleries.
import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import Views from './Views.vue'
import './style.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('Views', Views)
  },
} satisfies Theme
