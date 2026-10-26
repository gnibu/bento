// Lizard 1.24.2/1.24.3 crash in JavaScriptBindings.in_expression on the next call.
export async function load() {
  const { result } = renderHook(() => useAuth(), { wrapper: Wrapper });
  await waitFor(() => expect(result.current.loading).toBe(false));
}
