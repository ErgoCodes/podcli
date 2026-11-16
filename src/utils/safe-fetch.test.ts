import { describe, expect, it } from "vitest";
import { assertPublicUrl, isBlockedIp } from "./safe-fetch.js";

describe("isBlockedIp", () => {
  it.each(["127.0.0.1", "10.1.2.3", "169.254.169.254", "192.168.0.5", "172.20.0.1", "0.0.0.0", "::1", "fe80::1", "fc00::1", "::ffff:127.0.0.1", "::ffff:7f00:1"])(
    "blocks %s",
    (ip) => expect(isBlockedIp(ip)).toBe(true),
  );

  it.each(["8.8.8.8", "1.1.1.1", "2606:4700:4700::1111"])("allows %s", (ip) => expect(isBlockedIp(ip)).toBe(false));
});

describe("assertPublicUrl", () => {
  it.each([
    "http://localhost/x",
    "http://127.0.0.1/x",
    "http://2130706433/x",
    "http://0x7f.1/x",
    "http://[::ffff:7f00:1]/x",
    "http://169.254.169.254/latest/meta-data",
    "file:///etc/passwd",
  ])("rejects %s", async (u) => {
    await expect(assertPublicUrl(u)).rejects.toThrow();
  });

  it("accepts a public literal IP", async () => {
    await expect(assertPublicUrl("http://8.8.8.8/x")).resolves.toBeInstanceOf(URL);
  });
});
