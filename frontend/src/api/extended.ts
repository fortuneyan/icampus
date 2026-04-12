import request from '@/utils/request'

// ==================== 宿舍管理 ====================

export interface DormitoryBuilding {
  id: string
  name: string
  building_no: string
  floor_count: number
  building_type: string
  status: string
}

export interface DormitoryRoom {
  id: string
  dormitory_id: string
  room_no: string
  floor: number
  bed_count: number
  occupied_beds: number
  room_type: string
  status: string
}

export interface DormitoryAssignment {
  id: string
  student_id: string
  room_id: string
  bed_no: number
  academic_year: string
  semester: string
  status: string
}

export function getDormitoryBuildings(params?: {
  keyword?: string
  building_type?: string
  status?: string
  page?: number
  page_size?: number
}) {
  return request.get('/extended/dormitory/buildings', { params })
}

export function createDormitoryBuilding(data: any) {
  return request.post('/extended/dormitory/buildings', data)
}

export function getDormitoryRooms(params?: {
  dormitory_id?: string
  status?: string
  page?: number
  page_size?: number
}) {
  return request.get('/extended/dormitory/rooms', { params })
}

export function createDormitoryRoom(data: any) {
  return request.post('/extended/dormitory/rooms', data)
}

export function getDormitoryAssignments(params?: {
  student_id?: string
  academic_year?: string
  page?: number
  page_size?: number
}) {
  return request.get('/extended/dormitory/assignments', { params })
}

export function createDormitoryAssignment(data: any) {
  return request.post('/extended/dormitory/assignments', data)
}

// ==================== 图书管理 ====================

export interface Book {
  id: string
  isbn: string
  title: string
  author: string
  publisher: string
  category: string
  location: string
  total_copies: number
  available_copies: number
  status: string
}

export function getBooks(params?: {
  keyword?: string
  category?: string
  status?: string
  page?: number
  page_size?: number
}) {
  return request.get('/extended/library/books', { params })
}

export function createBook(data: any) {
  return request.post('/extended/library/books', data)
}

export function getBorrows(params?: {
  student_id?: string
  status?: string
  page?: number
  page_size?: number
}) {
  return request.get('/extended/library/borrows', { params })
}

export function createBorrow(data: any) {
  return request.post('/extended/library/borrows', data)
}

export function returnBook(borrowId: string) {
  return request.post(`/extended/library/borrows/${borrowId}/return`)
}

// ==================== 一卡通管理 ====================

export interface CampusCard {
  id: string
  card_no: string
  student_id?: string
  card_type: string
  balance: number
  status: string
}

export function getCards(params?: {
  keyword?: string
  card_type?: string
  status?: string
  page?: number
  page_size?: number
}) {
  return request.get('/extended/card/cards', { params })
}

export function createCard(data: any) {
  return request.post('/extended/card/cards', data)
}

export function rechargeCard(data: { card_id: string; transaction_type: string; amount: number }) {
  return request.post('/extended/card/transactions/recharge', data)
}

export function getTransactions(params?: {
  card_id?: string
  transaction_type?: string
  page?: number
  page_size?: number
}) {
  return request.get('/extended/card/transactions', { params })
}

// ==================== 奖助学金管理 ====================

export interface Scholarship {
  id: string
  name: string
  scholarship_no: string
  scholarship_type: string
  level: string
  amount: number
  quota: number
  academic_year: string
  semester: string
  status: string
}

export interface ScholarshipApplication {
  id: string
  scholarship_id: string
  student_id: string
  academic_year: string
  semester: string
  gpa: string
  rank: number
  status: string
}

export function getScholarships(params?: {
  keyword?: string
  scholarship_type?: string
  academic_year?: string
  status?: string
  page?: number
  page_size?: number
}) {
  return request.get('/extended/scholarship/projects', { params })
}

export function createScholarship(data: any) {
  return request.post('/extended/scholarship/projects', data)
}

export function getApplications(params?: {
  scholarship_id?: string
  student_id?: string
  status?: string
  page?: number
  page_size?: number
}) {
  return request.get('/extended/scholarship/applications', { params })
}

export function createApplication(data: any) {
  return request.post('/extended/scholarship/applications', data)
}

export function reviewApplication(applicationId: string, data: { status: string; comment?: string }) {
  return request.put(`/extended/scholarship/applications/${applicationId}/review`, null, { params: data })
}
