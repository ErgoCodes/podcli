import { lookup } from "dns/promises";
import { BlockList, isIP } from "net";

const blocked = new BlockList();

for (const [net, prefix] of [
  ["0.0.0.0", 8],
  ["10.0.0.0", 8],
  ["100.64.0.0", 10],
  ["127.0.0.0", 8],
  ["169.254.0.0", 16],
  ["172.16.0.0", 12],
  ["192.0.0.0", 24],
  ["192.168.0.0", 16],
  ["198.18.0.0", 15],
  ["224.0.0.0", 4],
  ["240.0.0.0", 4],
] as const) {
  blocked.addSubnet(net, prefix, "ipv4");
}

blocked.addAddress("::", "ipv6");
blocked.addAddress("::1", "ipv6");
blocked.addSubnet("fc00::", 7, "ipv6");
blocked.addSubnet("fe80::", 10, "ipv6");
blocked.addSubnet("ff00::", 8, "ipv6");

/** Extracts the IPv4 address from an IPv4-mapped IPv6 literal, if any. */
function unmapIPv4(ip: string): string | null {
  const dotted = /^::ffff:(\d+\.\d+\.\d+\.\d+)$/i.exec(ip);

  if (dotted) return dotted[1];

  const hex = /^::ffff:([0-9a-f]{1,4}):([0-9a-f]{1,4})$/i.exec(ip);

  if (hex) {
    const hi = parseInt(hex[1], 16);
    const lo = parseInt(hex[2], 16);

    return `${hi >> 8}.${hi & 255}.${lo >> 8}.${lo & 255}`;
  }

  return null;
}

export function isBlockedIp(ip: string): boolean {
  const family = isIP(ip);

  if (!family) return true;

  if (family === 6) {
    const v4 = unmapIPv4(ip);

    if (v4) return blocked.check(v4, "ipv4");
  }

  return blocked.check(ip, family === 4 ? "ipv4" : "ipv6");
}

/** Throws unless the URL is http(s) and every address its host resolves to is public. */
export async function assertPublicUrl(rawUrl: string): Promise<URL> {
  let parsed: URL;

  try {
    parsed = new URL(rawUrl);
  } catch {
    throw new Error(`Invalid URL: ${rawUrl}`);
  }

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error(`Unsupported URL protocol: ${parsed.protocol}`);
  }

  const host = parsed.hostname.replace(/^\[|\]$/g, "").toLowerCase();

  if (host === "localhost" || host.endsWith(".localhost")) {
    throw new Error(`Refusing to fetch from a private/loopback host: ${host}`);
  }

  const addresses = isIP(host) ? [{ address: host }] : await lookup(host, { all: true });

  if (addresses.length === 0 || addresses.some((a) => isBlockedIp(a.address))) {
    throw new Error(`Refusing to fetch from a private/loopback host: ${host}`);
  }

  return parsed;
}

const MAX_REDIRECTS = 5;

/** fetch() that validates the target and every redirect hop against assertPublicUrl. */
export async function safeFetch(rawUrl: string, init: RequestInit = {}): Promise<Response> {
  let url = rawUrl;

  for (let hop = 0; hop <= MAX_REDIRECTS; hop++) {
    await assertPublicUrl(url);
    const res = await fetch(url, { ...init, redirect: "manual" });

    if (res.status >= 300 && res.status < 400 && res.headers.get("location")) {
      url = new URL(res.headers.get("location") as string, url).toString();
      continue;
    }

    return res;
  }

  throw new Error(`Too many redirects fetching ${rawUrl}`);
}
