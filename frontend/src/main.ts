import { createApp } from 'vue'
import '@fontsource-variable/noto-sans-sc/index.css'
import { addIcon } from '@iconify/vue'
import activity from '@iconify-icons/lucide/activity'
import arrowLeft from '@iconify-icons/lucide/arrow-left'
import arrowRight from '@iconify-icons/lucide/arrow-right'
import arrowUpRight from '@iconify-icons/lucide/arrow-up-right'
import badgeAlert from '@iconify-icons/lucide/badge-alert'
import bell from '@iconify-icons/lucide/bell'
import bot from '@iconify-icons/lucide/bot'
import briefcaseBusiness from '@iconify-icons/lucide/briefcase'
import calculator from '@iconify-icons/lucide/calculator'
import chartNoAxesCombined from '@iconify-icons/lucide/line-chart'
import check from '@iconify-icons/lucide/check'
import chevronDown from '@iconify-icons/lucide/chevron-down'
import chevronRight from '@iconify-icons/lucide/chevron-right'
import circleCheck from '@iconify-icons/lucide/check-circle'
import circleDollarSign from '@iconify-icons/lucide/circle-dollar-sign'
import circleUserRound from '@iconify-icons/lucide/user-circle-2'
import clock3 from '@iconify-icons/lucide/clock-3'
import cloudOff from '@iconify-icons/lucide/cloud-off'
import copy from '@iconify-icons/lucide/copy'
import databaseSearch from '@iconify-icons/lucide/database'
import fileSearch from '@iconify-icons/lucide/file-search'
import history from '@iconify-icons/lucide/history'
import hourglass from '@iconify-icons/lucide/hourglass'
import house from '@iconify-icons/lucide/home'
import inbox from '@iconify-icons/lucide/inbox'
import info from '@iconify-icons/lucide/info'
import listChecks from '@iconify-icons/lucide/list-checks'
import messageSquarePlus from '@iconify-icons/lucide/message-square-plus'
import messagesSquare from '@iconify-icons/lucide/messages-square'
import panelRightClose from '@iconify-icons/lucide/panel-right-close'
import panelRightOpen from '@iconify-icons/lucide/panel-right-open'
import pause from '@iconify-icons/lucide/pause'
import play from '@iconify-icons/lucide/play'
import plus from '@iconify-icons/lucide/plus'
import radar from '@iconify-icons/lucide/radar'
import repeat2 from '@iconify-icons/lucide/repeat-2'
import route from '@iconify-icons/lucide/route'
import send from '@iconify-icons/lucide/send'
import sparkles from '@iconify-icons/lucide/sparkles'
import thumbsDown from '@iconify-icons/lucide/thumbs-down'
import thumbsUp from '@iconify-icons/lucide/thumbs-up'
import toolCase from '@iconify-icons/lucide/wrench'
import userRound from '@iconify-icons/lucide/user'
import wandSparkles from '@iconify-icons/lucide/wand-2'
import x from '@iconify-icons/lucide/x'
import './style.css'
import App from './App.vue'

const localIcons = {
  activity,
  'arrow-left': arrowLeft,
  'arrow-right': arrowRight,
  'arrow-up-right': arrowUpRight,
  'badge-alert': badgeAlert,
  bell,
  bot,
  'briefcase-business': briefcaseBusiness,
  calculator,
  'chart-no-axes-combined': chartNoAxesCombined,
  check,
  'chevron-down': chevronDown,
  'chevron-right': chevronRight,
  'circle-check': circleCheck,
  'circle-dollar-sign': circleDollarSign,
  'circle-user-round': circleUserRound,
  'clock-3': clock3,
  'cloud-off': cloudOff,
  copy,
  'database-search': databaseSearch,
  'file-search': fileSearch,
  history,
  hourglass,
  house,
  inbox,
  info,
  'list-checks': listChecks,
  'message-square-plus': messageSquarePlus,
  'messages-square': messagesSquare,
  'panel-right-close': panelRightClose,
  'panel-right-open': panelRightOpen,
  pause,
  play,
  plus,
  radar,
  'repeat-2': repeat2,
  route,
  send,
  sparkles,
  'thumbs-down': thumbsDown,
  'thumbs-up': thumbsUp,
  'tool-case': toolCase,
  'user-round': userRound,
  'wand-sparkles': wandSparkles,
  x,
}

Object.entries(localIcons).forEach(([name, data]) => addIcon(`lucide:${name}`, data))

createApp(App).mount('#app')
