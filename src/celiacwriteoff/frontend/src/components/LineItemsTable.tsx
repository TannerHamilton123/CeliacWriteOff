import { useEffect, useRef, useState } from 'react'
import {
  fetchCheapestInCategory,
  fetchSubstituteCategories,
  type SubstituteCategory,
} from '../api/substitutes'
import type { LineItem } from '../context/ItemsContext'

interface LineItemsTableProps {
  lineItems: LineItem[]
  /** Merge `changes` into the line item at `index`. Must use functional state updates,
   * since price lookups resolve after other edits may have happened. */
  onUpdateLineItem: (index: number, changes: Partial<LineItem>) => void
}

type PriceStatus = 'loading' | 'unavailable' | 'error'

function LineItemsTable({ lineItems, onUpdateLineItem }: LineItemsTableProps) {
  const [categories, setCategories] = useState<SubstituteCategory[]>([])
  const [priceStatus, setPriceStatus] = useState<Record<number, PriceStatus>>({})
  // The category most recently requested per row, so a slow response for an
  // earlier selection can't overwrite a newer one.
  const latestRequest = useRef<Record<number, string>>({})

  useEffect(() => {
    fetchSubstituteCategories()
      .then(setCategories)
      .catch(() => setCategories([]))
  }, [])

  if (lineItems.length === 0) return null

  function setStatus(index: number, status: PriceStatus | null) {
    setPriceStatus(prev => {
      const next = { ...prev }
      if (status) next[index] = status
      else delete next[index]
      return next
    })
  }

  function toggleGlutenSubstitute(index: number, li: LineItem) {
    if (li.is_gluten_substitute) {
      delete latestRequest.current[index]
      setStatus(index, null)
      onUpdateLineItem(index, {
        is_gluten_substitute: false,
        substitute_category: null,
        regular_product_name: null,
        regular_price: null,
      })
    } else {
      onUpdateLineItem(index, { is_gluten_substitute: true })
    }
  }

  async function selectCategory(index: number, category: string) {
    latestRequest.current[index] = category
    onUpdateLineItem(index, {
      substitute_category: category || null,
      regular_product_name: null,
      regular_price: null,
    })
    if (!category) {
      setStatus(index, null)
      return
    }

    setStatus(index, 'loading')
    try {
      const result = await fetchCheapestInCategory(category)
      if (latestRequest.current[index] !== category) return
      onUpdateLineItem(index, {
        regular_product_name: result.product_name,
        regular_price: result.price,
      })
      setStatus(index, result.price == null ? 'unavailable' : null)
    } catch {
      if (latestRequest.current[index] !== category) return
      setStatus(index, 'error')
    }
  }

  function renderRegularPrice(index: number, li: LineItem) {
    if (!li.is_gluten_substitute || !li.substitute_category) return '—'
    const status = priceStatus[index]
    if (status === 'loading') return 'Looking up…'
    if (status === 'error') return 'Lookup failed'
    if (li.regular_price == null) return 'Unavailable'
    return (
      <span title={li.regular_product_name ?? undefined}>${li.regular_price.toFixed(2)}</span>
    )
  }

  return (
    <div className="line-items-review">
      <p>Select any items below that are a gluten-free substitute purchase:</p>
      <div className="line-items-table-wrap">
        <table className="line-items-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Qty</th>
              <th>Price</th>
              <th>Gluten sub</th>
              <th>Product type</th>
              <th>Regular price</th>
            </tr>
          </thead>
          <tbody>
            {lineItems.map((li, i) => (
              <tr key={i}>
                <td>{li.item_name || '—'}</td>
                <td>{li.item_quantity ?? 1}</td>
                <td>${li.item_price?.toFixed(2) ?? '0.00'}</td>
                <td>
                  <button
                    type="button"
                    className={`bubble-toggle${li.is_gluten_substitute ? ' bubble-toggle-active' : ''}`}
                    role="checkbox"
                    aria-checked={li.is_gluten_substitute ? 'true' : 'false'}
                    aria-label={`Mark "${li.item_name || 'item'}" as a gluten substitute`}
                    onClick={() => toggleGlutenSubstitute(i, li)}
                  />
                </td>
                <td>
                  {li.is_gluten_substitute ? (
                    <select
                      aria-label={`Product type for "${li.item_name || 'item'}"`}
                      value={li.substitute_category ?? ''}
                      onChange={e => selectCategory(i, e.target.value)}
                    >
                      <option value="">Select type…</option>
                      {categories.map(c => (
                        <option key={c.key} value={c.key}>
                          {c.label}
                        </option>
                      ))}
                    </select>
                  ) : (
                    '—'
                  )}
                </td>
                <td>{renderRegularPrice(i, li)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default LineItemsTable
