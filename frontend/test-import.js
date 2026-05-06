import { getTreeById, getRuneById, getRuneIconUrl } from './src/data/runes.js'

console.log('getTreeById:', typeof getTreeById)
console.log('getRuneById:', typeof getRuneById)
console.log('getRuneIconUrl:', typeof getRuneIconUrl)

const tree = getTreeById(8000)
console.log('Tree 8000:', tree)
