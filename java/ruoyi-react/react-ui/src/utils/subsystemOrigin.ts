/** Public nginx gateway. See deploy/nginx/nginx.conf */

function cleanOverride(envOverride?: string): string | undefined {
  const o = (envOverride ?? '').trim();
  if (!o || o === 'undefined' || o === 'null') return undefined;
  return o.replace(/\/$/, '');
}

/**
 * ??? iframe?
 * ???????????? /gw/<slug>?https://geime.fun ???? :18080?
 * ??????? HTTP??????????????????
 */
export function resolveSubsystemEntry(opts: {
  slug: string;
  port: number;
  envOverride?: string;
}): string {
  const override = cleanOverride(opts.envOverride);
  if (override) {
    if (/^https?:\/\//i.test(override)) return override;
    if (override.startsWith('/')) return override;
  }
  if (typeof window === 'undefined') return `http://127.0.0.1:${opts.port}`;
  const { hostname } = window.location;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return `http://127.0.0.1:${opts.port}`;
  }
  return `/gw/${opts.slug}`;
}

/** Python Agent????? / ????? */
export function resolveAgentOrigin(envOverride?: string): string {
  return resolveSubsystemEntry({
    slug: 'agent',
    port: 8080,
    envOverride,
  });
}
