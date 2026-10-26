// Lizard 1.24.2/1.24.3 crash in JavaScriptBindings.in_expression on the next call.
export function migrate(instance: unknown) {
  (instance as { migrate(): void }).migrate();
  verify();
}
