export type RecentDocument = {
  id: number
  title: string
  company: string
  documentType: string
  fiscalYear: number
  uploadedAt: string
  status: 'Processed' | 'Processing' | 'Failed'
}

export const MOCK_RECENT_DOCUMENTS: RecentDocument[] = [
  {
    id: 1,
    title: 'Apple Inc. Form 10-K FY2024',
    company: 'Apple Inc.',
    documentType: '10-K',
    fiscalYear: 2024,
    uploadedAt: 'Aug 21, 2026',
    status: 'Processed',
  },
  {
    id: 2,
    title: 'Microsoft Corp. Q3 10-Q',
    company: 'Microsoft Corp.',
    documentType: '10-Q',
    fiscalYear: 2026,
    uploadedAt: 'Aug 19, 2026',
    status: 'Processed',
  },
  {
    id: 3,
    title: 'NVIDIA Corp. Form 10-K FY2026',
    company: 'NVIDIA Corp.',
    documentType: '10-K',
    fiscalYear: 2026,
    uploadedAt: 'Aug 15, 2026',
    status: 'Processing',
  },
  {
    id: 4,
    title: 'Amazon.com Inc. Q2 Earnings Release',
    company: 'Amazon.com Inc.',
    documentType: '8-K',
    fiscalYear: 2026,
    uploadedAt: 'Aug 12, 2026',
    status: 'Processed',
  },
  {
    id: 5,
    title: 'Tesla Inc. Annual Report FY2025',
    company: 'Tesla Inc.',
    documentType: '10-K',
    fiscalYear: 2025,
    uploadedAt: 'Aug 08, 2026',
    status: 'Failed',
  },
]
