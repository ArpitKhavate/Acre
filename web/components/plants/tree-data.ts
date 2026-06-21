/** Stick scan tree — viewBox 100 × 560, trunk center x = 50. */

export const TREE_HEIGHT = 560
export const TREE_CENTER_X = 50

export const TREE_BRANCHES = [
  'M50 95 Q38 98 22 108',
  'M50 195 Q62 198 78 208',
  'M50 295 Q38 298 22 308',
  'M50 395 Q62 398 78 408',
  'M50 495 Q38 498 22 508',
] as const

export const TREE_LEAF_YS = [80, 160, 260, 360, 460] as const

/** Side metadata for alternating readout cards. */
export const TREE_LIMBS = TREE_BRANCHES.map((branch, i) => ({
  side: (i % 2 === 0 ? 'left' : 'right') as 'left' | 'right',
  junctionY: [95, 195, 295, 395, 495][i],
  branch,
})) as const
