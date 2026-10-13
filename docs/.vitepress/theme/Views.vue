<script setup lang="ts">
// A grid of rendered views. Entries are [view, caption, link?]; a view is a path under /img/
// (line drawings, .svg) or, with `photo`, under /photo/ (Blender renders, .webp), without the
// extension -- or a bare view name when `design` is set:
//   <Views design="split" :views="[['side', 'Side'], ['seam', 'Seam']]" />
//   <Views photo design="split" :views="[['hero', 'Split case']]" />
//   <Views :views="[['split/detail', 'Split case', './split']]" />
import { withBase } from 'vitepress'

const props = defineProps<{
  design?: string
  views: [string, string, string?][]
  cols?: number
  photo?: boolean
}>()

const src = (view: string) => {
  const [root, ext] = props.photo ? ['photo', 'webp'] : ['img', 'svg']
  return withBase(`/${root}/${props.design ? `${props.design}/` : ''}${view}.${ext}`)
}
</script>

<template>
  <div class="dais-views" :style="{ '--dais-cols': cols ?? 2 }">
    <figure v-for="[view, caption, link] in views" :key="view" class="dais-view">
      <a :href="link ?? src(view)" :target="link ? undefined : '_blank'" rel="noopener">
        <img :src="src(view)" :alt="caption" loading="lazy" />
      </a>
      <figcaption>{{ caption }}</figcaption>
    </figure>
  </div>
</template>
