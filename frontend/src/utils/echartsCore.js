import * as echarts from 'echarts/core'
import { LineChart, RadarChart } from 'echarts/charts'
import { GridComponent, LegendComponent, RadarComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

let registered = false

export function getEcharts() {
  if (!registered) {
    echarts.use([
      LineChart,
      RadarChart,
      GridComponent,
      LegendComponent,
      RadarComponent,
      TooltipComponent,
      CanvasRenderer,
    ])
    registered = true
  }
  return echarts
}
