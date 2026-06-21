import { SplitText } from '@/components/primitives'
import { PlantSvg, type PlantVariant } from './plant-svg'
import { TreeIllustration } from './tree-svg'

const NODES: {
  step: string
  title: string
  body: string
  variant: PlantVariant
  telemetry: string
}[] = [
  {
    step: '01',
    title: 'Point at the crop',
    body: 'Zone marker lands in-frame. The detector locks the plant crop and reads leaf color.',
    variant: 'healthy',
    telemetry: 'ZONE:Z2 · crop locked',
  },
  {
    step: '02',
    title: 'Score the health',
    body: 'Weeds, discoloration, disease, pest, and humidity fold into a 0–100 score on the LCD.',
    variant: 'healthy',
    telemetry: 'HEALTH:94 · LCD update',
  },
  {
    step: '03',
    title: 'Spot the disease',
    body: 'Symptoms map to an offline cure — pesticide, organic alt, and spray notes from UC IPM.',
    variant: 'disease',
    telemetry: 'early_blight · 0.87 conf',
  },
  {
    step: '04',
    title: 'Catch the pest',
    body: 'RGB goes red when a pest is present. Green means pest-free — instant field call.',
    variant: 'weed',
    telemetry: 'LED:RED · aphid detected',
  },
  {
    step: '05',
    title: 'Log & sync later',
    body: 'Every scan hits local SQLite first. Sync pushes when the field finds a signal.',
    variant: 'healthy',
    telemetry: 'SQLite · synced:0',
  },
]

export function TreeScrollStory() {
  return (
    <section
      id="scan-story"
      data-tree-story
      className="relative overflow-hidden bg-paper py-20 md:py-28"
      aria-label="Scan pipeline — growing tree"
    >
      <div className="dot-grid pointer-events-none absolute inset-0 opacity-50" />

      <div className="relative mx-auto max-w-5xl px-5 md:px-8">
        <div className="mb-16 max-w-lg">
          <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-green">
            Scroll — watch the tree grow
          </p>
          <SplitText
            as="h2"
            text="From root to readout."
            className="mt-4 font-display text-4xl font-semibold leading-[1.05] tracking-tight text-ink md:text-5xl"
          />
          <p className="mt-4 text-[15px] leading-relaxed text-muted">
            Each branch is a step in the scan loop — point, score, diagnose, flag, log.
          </p>
        </div>

        <div className="relative">
          <TreeIllustration className="pointer-events-none absolute left-1/2 top-0 hidden h-full w-28 -translate-x-1/2 md:block lg:w-32" />

          <div
            className="absolute bottom-0 left-4 top-0 w-0.5 bg-gradient-to-b from-green/20 via-green to-soil/40 md:hidden"
            aria-hidden
          />

          <div className="relative space-y-16 md:space-y-24">
            {NODES.map((node, i) => {
              const left = i % 2 === 0
              return (
                <div
                  key={node.step}
                  className="grid grid-cols-1 items-start md:grid-cols-[1fr_2.5rem_1fr] md:gap-x-2"
                >
                  {left ? (
                    <>
                      <article
                        data-tree-node
                        data-tree-side="left"
                        data-tree-index={i}
                        className="md:col-start-1 md:max-w-md md:justify-self-end"
                      >
                        <NodeCard node={node} showHealthBar={i === 1} />
                      </article>
                      <span
                        data-tree-dot
                        data-branch-index={i}
                        className="relative z-10 mx-auto mt-10 hidden size-3 rounded-full border-2 border-paper bg-leaf shadow-[0_0_14px_rgba(65,216,105,0.55)] md:col-start-2 md:block"
                      />
                      <div className="hidden md:col-start-3 md:block" aria-hidden />
                    </>
                  ) : (
                    <>
                      <div className="hidden md:col-start-1 md:block" aria-hidden />
                      <span
                        data-tree-dot
                        data-branch-index={i}
                        className="relative z-10 mx-auto mt-10 hidden size-3 rounded-full border-2 border-paper bg-leaf shadow-[0_0_14px_rgba(65,216,105,0.55)] md:col-start-2 md:block"
                      />
                      <article
                        data-tree-node
                        data-tree-side="right"
                        data-tree-index={i}
                        className="md:col-start-3 md:max-w-md"
                      >
                        <NodeCard node={node} showHealthBar={i === 1} />
                      </article>
                    </>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}

function NodeCard({
  node,
  showHealthBar,
}: {
  node: (typeof NODES)[number]
  showHealthBar?: boolean
}) {
  return (
    <div className="card-soft tree-node-card w-full rounded-card border border-line bg-card p-6 md:p-7">
      <div className="flex items-start gap-4">
        <PlantSvg variant={node.variant} size={72} className="plant-sway shrink-0" />
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <span className="font-mono text-[10px] uppercase tracking-wider text-green">
              {node.telemetry}
            </span>
            <span className="font-mono text-xs text-ink/20">{node.step}</span>
          </div>
          <h3 className="mt-2 font-display text-xl font-semibold text-ink">{node.title}</h3>
          <p className="mt-2 text-sm leading-relaxed text-muted">{node.body}</p>
          {showHealthBar && (
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-line">
              <div
                data-tree-health-bar
                className="h-full w-0 rounded-full bg-gradient-to-r from-green to-leaf"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
