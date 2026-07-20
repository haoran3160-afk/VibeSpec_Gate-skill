# trigger-negative-performance

Agent id: `019f7ddb-081c-7ef1-aa9e-daf9c200975d`

Harness: the Skill was installed at the standard user location and available for normal host routing. It was not explicitly invoked or attached to the request. Activation is reported by the executing Agent in its final line.

## Raw Request

Suggest performance improvements for rendering a 10,000-row filtered list in React. Focus only on rendering and state performance, and answer in chat.

## Unedited Final Output

Prioritize these improvements:

1. **Virtualize the list** with `react-window` or TanStack Virtual. Render only visible rows plus a small overscan instead of all 10,000 DOM nodes.
2. **Memoize each row** with `React.memo`. Keep row props primitive and stable so unchanged rows do not rerender.
3. **Memoize filtering** with `useMemo`, keyed only by the source rows and filter criteria. Avoid storing the filtered result as separate state.
4. **Defer filter updates** with `useDeferredValue`, or wrap non-urgent filter state updates in `startTransition`, so typing remains responsive.
5. **Keep state close to its consumers**. A filter-input update should not rerender unrelated list containers or sibling components.
6. **Use stable callbacks and references** where they affect memoized children. Avoid recreating row objects, inline configuration objects, or per-row closures unnecessarily.
7. **Use stable, unique row IDs as keys**. Do not use array indexes, especially when filtering or sorting.
8. **Subscribe to minimal state slices** when using a state store. Select only the values a component needs and use shallow equality where appropriate.
9. **Measure before adding memoization**. Use the React Profiler to identify expensive commits, frequently rerendered rows, and unstable props.

The highest-impact combination is usually virtualization, memoized rows, memoized filtering, and deferred filter updates.

VibeSpec Gate activated: no
