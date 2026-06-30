/**
 * Derive a human-readable display label for an OPC node.
 *
 * Resolution order:
 * 1. ``node.display_name`` (explicit override)
 * 2. The last dot-segment of ``node.node_id`` (e.g. ``Shearer.left_motor.current`` → ``current``)
 * 3. ``node.node_id`` itself (fallback when node_id has no dots or is empty)
 *
 * Extracted as a shared helper — previously the same expression was
 * copy-pasted across ``NodeRow``, ``NodeCard``, and ``useFilteredNodes``.
 */
export function nodeLabel(node) {
  if (!node) return ''
  return node.display_name || (node.node_id || '').split('.').pop() || node.node_id || ''
}
