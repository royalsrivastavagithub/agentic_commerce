export function buildSortParams(sort: string): string {
  if (sort === "default") return ""
  if (sort === "price-asc") return "&sort_by=price&sort_order=asc"
  if (sort === "price-desc") return "&sort_by=price&sort_order=desc"
  if (sort === "rating") return "&sort_by=rating&sort_order=desc"
  if (sort === "title-asc") return "&sort_by=title&sort_order=asc"
  if (sort === "title-desc") return "&sort_by=title&sort_order=desc"
  if (sort === "discount") return "&sort_by=discount&sort_order=desc"
  return ""
}

export function buildFilterParams(
  minPrice: string,
  maxPrice: string,
  minRating: number,
  minDiscount: number,
  priceMin: number,
  priceMax: number,
): string {
  let s = ""
  if (minPrice && parseFloat(minPrice) > priceMin) s += `&min_price=${parseFloat(minPrice)}`
  if (maxPrice && parseFloat(maxPrice) < priceMax) s += `&max_price=${parseFloat(maxPrice)}`
  if (minRating > 0) s += `&min_rating=${minRating}`
  if (minDiscount > 0) s += `&min_discount=${minDiscount}`
  return s
}
