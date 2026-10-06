import type { Product } from './types.ts'

/** Shopper-facing categories. `kind` matches the backend's garment_kind() (the `kind` field on each product). */
export interface Category {
  slug: string
  kind: string
  label: string
  blurb: string
}

export const CATEGORIES: Category[] = [
  { slug: 'hoodies', kind: 'hoodie', label: 'Hoodies', blurb: 'Pullovers and full-zips for cold walks to class.' },
  { slug: 'crewnecks', kind: 'crewneck', label: 'Crewnecks', blurb: 'The classic Yale sweatshirt, in a lot of designs.' },
  { slug: 'quarter-zips', kind: 'quarter-zip', label: 'Quarter-Zips', blurb: 'A little dressier. Good for parents’ weekend.' },
  { slug: 't-shirts', kind: 't-shirt', label: 'T-Shirts', blurb: 'Easy tees for game days and everything else.' },
  { slug: 'long-sleeve', kind: 'long-sleeve', label: 'Long Sleeve', blurb: 'Lightweight long sleeves for in-between weather.' },
  { slug: 'jackets', kind: 'jacket', label: 'Jackets & Fleece', blurb: 'Fleece and jackets for when it actually gets cold.' },
]

export function categoryBySlug(slug: string | null): Category | null {
  return CATEGORIES.find((category) => category.slug === slug) ?? null
}

export function categoryByKind(kind: string | undefined): Category | null {
  return CATEGORIES.find((category) => category.kind === kind) ?? null
}

/** Shop-by collections. `slug` matches the backend's COLLECTIONS (the `collections` field on each product). */
export interface Collection {
  slug: string
  label: string
  blurb: string
  /** A product whose photo represents the collection on the home page tiles. */
  coverProduct: string
}

export const COLLECTIONS: Collection[] = [
  {
    slug: 'colleges',
    label: 'Residential Colleges',
    blurb: 'Rep your college, from Berkeley to Trumbull.',
    coverProduct: 'saybrook-college-crewneck',
  },
  {
    slug: 'sports',
    label: 'Sports & Teams',
    blurb: 'Gear for game day and every Bulldog team.',
    coverProduct: 'yale-sports-hoodie-hockey',
  },
  {
    slug: 'family',
    label: 'Yale Family',
    blurb: 'Mom, Dad, Grandpa, and the rest of the crew.',
    coverProduct: 'yale-dad-hoodie',
  },
  {
    slug: 'schools',
    label: 'Grad & Professional Schools',
    blurb: 'SOM, Law, Med, Art, Architecture, and more.',
    coverProduct: 'school-of-management-crest-t-shirt',
  },
  {
    slug: 'classics',
    label: 'Classic Yale',
    blurb: 'Vintage bulldogs, big YALE, and timeless picks.',
    coverProduct: 'district-vit-hoodie-vintage-bulldog',
  },
]

export function collectionBySlug(slug: string | null): Collection | null {
  return COLLECTIONS.find((collection) => collection.slug === slug) ?? null
}

export type SortKey = 'featured' | 'price-asc' | 'price-desc' | 'name-asc' | 'name-desc'

export const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: 'featured', label: 'Featured' },
  { value: 'price-asc', label: 'Price: Low to High' },
  { value: 'price-desc', label: 'Price: High to Low' },
  { value: 'name-asc', label: 'Name: A to Z' },
  { value: 'name-desc', label: 'Name: Z to A' },
]

export function sortKey(value: string | null): SortKey {
  return SORT_OPTIONS.some((option) => option.value === value) ? (value as SortKey) : 'featured'
}

/** "Featured" keeps the catalogue's own order (A to Z); price sorts break ties by name. */
export function sortProducts(products: Product[], sort: SortKey): Product[] {
  const byName = (a: Product, b: Product) => a.name.localeCompare(b.name)
  const sorted = [...products]
  switch (sort) {
    case 'price-asc':
      return sorted.sort((a, b) => a.price - b.price || byName(a, b))
    case 'price-desc':
      return sorted.sort((a, b) => b.price - a.price || byName(a, b))
    case 'name-desc':
      return sorted.sort((a, b) => byName(b, a))
    default:
      return sorted.sort(byName)
  }
}
