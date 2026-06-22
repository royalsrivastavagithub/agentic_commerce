export interface User {
  id: number
  email: string
  first_name?: string
  last_name?: string
  phone?: string
  date_of_birth?: string
  gender?: string
  role: string
  is_active: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Category {
  id: number
  name: string
}

export interface Product {
  id: number
  title: string
  description: string
  category_id: number
  price: number
  discount_percentage: number
  rating: number
  review_count: number
  stock: number
  tags: string[]
  brand?: string
  sku: string
  weight: number
  dimensions: Record<string, number>
  warranty_information: string
  shipping_information: string
  availability_status: string
  return_policy: string
  minimum_order_quantity: number
  meta: Record<string, string>
  images: string[]
  thumbnail: string
  category?: string
  is_featured: boolean
}

export interface ProductListResponse {
  products: Product[]
  total: number
  skip: number
  limit: number
}

export interface CartItem {
  id: number
  cart_id: number
  product_id: number
  quantity: number
  product: Product
}

export interface Cart {
  id: number
  items: CartItem[]
  total: number
  created_at: string
  updated_at: string
}

export interface SavedItem {
  id: number
  product_id: number
  saved_at: string
  product: Product
}

export interface Address {
  id: number
  label: string
  street: string
  city: string
  state: string
  pincode: string
  country: string
  is_default: boolean
  address_type: "home" | "work" | "other"
}

export interface Order {
  id: number
  user_id: number
  status: string
  shipping_name: string
  shipping_phone: string
  shipping_address_line_1: string
  shipping_address_line_2?: string
  shipping_city: string
  shipping_state: string
  shipping_country: string
  shipping_pincode: string
  subtotal: number
  total: number
  created_at: string
  updated_at: string
  razorpay_order_id?: string
  razorpay_payment_id?: string
  payment_status?: string
  items: OrderItem[]
}

export interface OrderItem {
  id: number
  product_id: number
  product_name: string
  product_price: number
  quantity: number
  subtotal: number
}

export interface Review {
  id: number
  user_id: number
  product_id: number
  rating: number
  comment: string
  created_at: string
  updated_at: string
  user?: { id: number; email: string; first_name?: string; last_name?: string }
}

export interface WishlistItem {
  id: number
  product_id: number
  created_at: string
  product: Product
}

export interface DashboardSummary {
  total_users: number
  total_products: number
  total_orders: number
  total_revenue: number
  average_order_value: number
  low_stock_count: number
  orders_by_status: Record<string, number>
}

export interface CreatePaymentResponse {
  order_id: number
  razorpay_order_id: string
  amount: number
  currency: string
  razorpay_key_id: string
}

export interface RevenuePoint {
  date: string
  revenue: number
}
