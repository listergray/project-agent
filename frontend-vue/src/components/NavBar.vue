<script setup lang="ts">
import { RouterLink } from 'vue-router'
import brandMark from '../assets/brand-mark.svg'

defineProps<{ right?: boolean }>()
</script>

<template>
  <nav class="nav">
    <RouterLink class="brand" to="/">
      <img class="brand-logo" :src="brandMark" alt="" width="34" height="34" />
      <span>Project Agent</span>
    </RouterLink>
    <div style="display: flex; align-items: center; gap: 8px">
      <slot name="right" />
    </div>
  </nav>
</template>
