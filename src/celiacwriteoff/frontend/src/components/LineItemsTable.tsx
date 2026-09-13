import type { LineItem } from '../context/ItemsContext'

interface LineItemsTableProps {
  lineItems: LineItem[]
  onToggleGlutenSubstitute: (index: number) => void
}

function LineItemsTable({ lineItems, onToggleGlutenSubstitute }: LineItemsTableProps) {
  if (lineItems.length === 0) return null

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
                    onClick={() => onToggleGlutenSubstitute(i)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default LineItemsTable
