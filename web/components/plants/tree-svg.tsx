import { TREE_BRANCHES, TREE_HEIGHT, TREE_LEAF_YS } from './tree-data'

export { TREE_HEIGHT, TREE_CENTER_X, TREE_LIMBS, TREE_BRANCHES } from './tree-data'

/** Minimal stick tree — stroke trunk, line branches, dot leaves. */
export function TreeIllustration({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox={`0 0 100 ${TREE_HEIGHT}`}
      preserveAspectRatio="none"
      aria-hidden
    >
      <g data-tree-root opacity={0.6}>
        <path
          d="M50 540 Q42 548 34 552 M50 540 Q58 548 66 552"
          fill="none"
          stroke="#6b4f2a"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </g>

      <path
        data-tree-trunk
        d="M50 20 Q49 280 50 540"
        fill="none"
        stroke="#15703e"
        strokeWidth="3.5"
        strokeLinecap="round"
      />

      {TREE_BRANCHES.map((d, i) => (
        <path
          key={i}
          data-tree-branch
          data-branch-index={i}
          d={d}
          fill="none"
          stroke="#41d869"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
      ))}

      {TREE_LEAF_YS.map((y, i) => (
        <circle
          key={i}
          data-tree-leaf
          cx={50 + (i % 2 === 0 ? -8 : 8)}
          cy={y}
          r="5"
          fill="#9fe0b3"
        />
      ))}
    </svg>
  )
}
