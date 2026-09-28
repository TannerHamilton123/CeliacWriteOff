const API_URL = import.meta.env.VITE_API_URL

export interface SubstituteCategory {
  key: string
  label: string
}

export interface CategoryPrice {
  category: string
  product_name: string | null
  size: string | null
  price: number | null
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { credentials: 'include' })
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`)
  }
  return response.json()
}

export function fetchSubstituteCategories(): Promise<SubstituteCategory[]> {
  return getJson('/substitutes/categories')
}

/** Cheapest regular (non-gluten-free) product in the category at the configured Kroger store. */
export function fetchCheapestInCategory(category: string): Promise<CategoryPrice> {
  return getJson(`/substitutes/categories/${encodeURIComponent(category)}/cheapest`)
}
