/** Build a fetch-compatible Response stub for unit tests. */
export function mockJsonResponse(status: number, body: unknown): Response {
  const text = JSON.stringify(body);
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers(),
    json: async () => JSON.parse(text),
    text: async () => text,
    blob: async () => new Blob([text]),
  } as unknown as Response;
}
