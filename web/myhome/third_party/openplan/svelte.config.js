import adapter from '@sveltejs/adapter-static'

/** @type {import('@sveltejs/kit').Config} */
const config = {
  kit: {
    adapter: adapter({
      pages: '../../public/openplan',
      assets: '../../public/openplan',
      fallback: 'index.html',
      precompress: false,
      strict: false,
    }),
    paths: {
      base: '/openplan',
    },
  },
}

export default config
