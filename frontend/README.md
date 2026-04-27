# Review Pulse Frontend

A modern React-based web application for the Review Pulse system, providing an intuitive dashboard for monitoring product reviews, analysis results, and report generation.

## 🚀 Features

### Core Functionality
- **Dashboard Overview**: Real-time metrics and system status
- **Review Management**: Browse, filter, and search reviews
- **Analysis Visualization**: Interactive charts and clustering results
- **Report Generation**: Create and download custom reports
- **Stakeholder Management**: Configure delivery settings
- **System Monitoring**: Performance metrics and health checks

### User Interface
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark/Light Mode**: Toggle between themes
- **Real-time Updates**: WebSocket for live data
- **Interactive Charts**: D3.js and Chart.js visualizations
- **Export Options**: PDF, Excel, CSV downloads

## 🛠️ Technology Stack

### Frontend Framework
- **React 18**: Modern hooks and concurrent features
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and development server
- **React Router**: Client-side routing

### UI Components
- **Tailwind CSS**: Utility-first styling
- **Headless UI**: Accessible component library
- **React Hook Form**: Form handling
- **React Query**: Server state management
- **Framer Motion**: Smooth animations

### Data Visualization
- **Chart.js**: Charts and graphs
- **D3.js**: Advanced visualizations
- **React Flow**: Clustering visualization
- **React Table**: Data tables

### State Management
- **Zustand**: Lightweight state management
- **React Query**: Server state and caching
- **React Hook Form**: Form state

### Development Tools
- **ESLint**: Code linting
- **Prettier**: Code formatting
- **Husky**: Git hooks
- **Vitest**: Unit testing
- **Playwright**: E2E testing

## 📦 Installation

### Prerequisites
- Node.js 18+
- npm or yarn
- Review Pulse backend running

### Quick Start

```bash
# Clone the repository
git clone https://github.com/Akash1122-cl/Akashmilestone-3-.git
cd Akashmilestone-3-/frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Create `.env.local`:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=10000

# WebSocket Configuration
VITE_WS_URL=ws://localhost:8000/ws

# Authentication
VITE_AUTH_ENABLED=true
VITE_AUTH_PROVIDER=auth0

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_EXPORTS=true
VITE_ENABLE_REAL_TIME=true

# Monitoring
VITE_SENTRY_DSN=your_sentry_dsn
VITE_ENABLE_DEBUG=false
```

## 🏗️ Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/         # Reusable components
│   │   ├── ui/            # Basic UI components
│   │   ├── charts/        # Chart components
│   │   ├── forms/         # Form components
│   │   └── layout/        # Layout components
│   ├── pages/             # Page components
│   │   ├── Dashboard/     # Main dashboard
│   │   ├── Reviews/       # Review management
│   │   ├── Analysis/      # Analysis results
│   │   ├── Reports/       # Report generation
│   │   ├── Settings/      # Application settings
│   │   └── Auth/          # Authentication pages
│   ├── hooks/             # Custom React hooks
│   ├── services/          # API services
│   ├── stores/            # State management
│   ├── utils/             # Utility functions
│   ├── types/             # TypeScript types
│   ├── constants/         # Application constants
│   └── styles/            # Global styles
├── tests/                 # Test files
├── docs/                  # Documentation
└── config/                # Configuration files
```

## 🧩 Components

### Core Components

#### Dashboard
```typescript
interface DashboardProps {
  timeRange: TimeRange;
  refreshInterval: number;
}

const Dashboard: React.FC<DashboardProps> = ({
  timeRange,
  refreshInterval
}) => {
  // Real-time metrics display
  // System health indicators
  // Quick action buttons
};
```

#### Review Management
```typescript
interface ReviewListProps {
  filters: ReviewFilters;
  pagination: PaginationConfig;
}

const ReviewList: React.FC<ReviewListProps> = ({
  filters,
  pagination
}) => {
  // Review table with sorting
  // Advanced filtering
  // Bulk actions
};
```

#### Analysis Visualization
```typescript
interface AnalysisViewProps {
  analysisId: string;
  visualizationType: 'clusters' | 'themes' | 'trends';
}

const AnalysisView: React.FC<AnalysisViewProps> = ({
  analysisId,
  visualizationType
}) => {
  // Interactive clustering visualization
  // Theme distribution charts
  // Trend analysis graphs
};
```

### UI Components

#### Data Tables
```typescript
interface DataTableProps<T> {
  data: T[];
  columns: ColumnConfig<T>[];
  loading?: boolean;
  pagination?: PaginationConfig;
  onRowClick?: (row: T) => void;
}

const DataTable = <T,>({
  data,
  columns,
  loading,
  pagination,
  onRowClick
}: DataTableProps<T>) => {
  // Sortable columns
  // Row selection
  // Virtual scrolling for large datasets
};
```

#### Charts
```typescript
interface ChartProps {
  type: 'line' | 'bar' | 'pie' | 'scatter';
  data: ChartData;
  options?: ChartOptions;
  responsive?: boolean;
}

const Chart: React.FC<ChartProps> = ({
  type,
  data,
  options,
  responsive = true
}) => {
  // Chart.js integration
  // Responsive design
  // Interactive tooltips
};
```

## 🔄 State Management

### Global State (Zustand)
```typescript
interface AppState {
  // User state
  user: User | null;
  isAuthenticated: boolean;
  
  // UI state
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  
  // Data state
  reviews: Review[];
  analyses: Analysis[];
  reports: Report[];
  
  // Actions
  setUser: (user: User | null) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  toggleSidebar: () => void;
}

const useAppStore = create<AppState>((set) => ({
  user: null,
  isAuthenticated: false,
  theme: 'light',
  sidebarOpen: true,
  reviews: [],
  analyses: [],
  reports: [],
  setUser: (user) => set({ user }),
  setTheme: (theme) => set({ theme }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen }))
}));
```

### Server State (React Query)
```typescript
// API hooks
export const useReviews = (filters: ReviewFilters) => {
  return useQuery({
    queryKey: ['reviews', filters],
    queryFn: () => reviewsApi.getReviews(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 60 * 1000 // 1 minute
  });
};

export const useAnalysis = (analysisId: string) => {
  return useQuery({
    queryKey: ['analysis', analysisId],
    queryFn: () => analysisApi.getAnalysis(analysisId),
    enabled: !!analysisId
  });
};
```

## 🎨 Styling

### Tailwind CSS Configuration
```javascript
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eff6ff',
          500: '#3b82f6',
          900: '#1e3a8a'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif']
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography')
  ]
};
```

### Component Styling
```typescript
// Example component with Tailwind
const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  children,
  ...props
}) => {
  const baseClasses = 'font-medium rounded-lg transition-colors';
  const variantClasses = {
    primary: 'bg-brand-500 text-white hover:bg-brand-600',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300',
    outline: 'border border-brand-500 text-brand-500 hover:bg-brand-50'
  };
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };
  
  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]}`}
      {...props}
    >
      {children}
    </button>
  );
};
```

## 📱 Responsive Design

### Breakpoints
```typescript
const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px'
};
```

### Mobile-First Approach
```typescript
// Responsive component example
const DashboardGrid: React.FC = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {/* Cards that adapt to screen size */}
    </div>
  );
};
```

## 🔐 Authentication

### Auth0 Integration
```typescript
// Auth configuration
const authConfig = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN,
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
  redirectUri: window.location.origin
};

// Auth hook
export const useAuth = () => {
  const { user, isAuthenticated } = useAppStore();
  
  const login = async () => {
    // Auth0 login flow
  };
  
  const logout = async () => {
    // Auth0 logout
  };
  
  return { user, isAuthenticated, login, logout };
};
```

### Protected Routes
```typescript
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};
```

## 📊 Data Visualization

### Chart Components
```typescript
// Sentiment trend chart
const SentimentChart: React.FC<{ data: SentimentData[] }> = ({ data }) => {
  const chartData = {
    labels: data.map(d => d.date),
    datasets: [
      {
        label: 'Positive',
        data: data.map(d => d.positive),
        borderColor: '#10b981',
        backgroundColor: '#10b98120'
      },
      {
        label: 'Negative',
        data: data.map(d => d.negative),
        borderColor: '#ef4444',
        backgroundColor: '#ef444420'
      }
    ]
  };
  
  return <Line data={chartData} options={chartOptions} />;
};

// Clustering visualization
const ClusterVisualization: React.FC<{ clusters: Cluster[] }> = ({
  clusters
}) => {
  // D3.js or React Flow implementation
  return (
    <div className="cluster-viz">
      {/* Interactive cluster diagram */}
    </div>
  );
};
```

## 🚀 Performance Optimization

### Code Splitting
```typescript
// Lazy loading routes
const Dashboard = lazy(() => import('../pages/Dashboard'));
const Reviews = lazy(() => import('../pages/Reviews'));
const Analysis = lazy(() => import('../pages/Analysis'));

// Suspense wrapper
const AppRoutes = () => (
  <Suspense fallback={<LoadingSpinner />}>
    <Routes>
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/reviews" element={<Reviews />} />
      <Route path="/analysis" element={<Analysis />} />
    </Routes>
  </Suspense>
);
```

### Virtual Scrolling
```typescript
// For large data tables
const VirtualizedTable: React.FC<{ items: any[] }> = ({ items }) => {
  return (
    <FixedSizeList
      height={600}
      itemCount={items.length}
      itemSize={50}
      itemData={items}
    >
      {({ index, style, data }) => (
        <div style={style}>
          <TableRow data={data[index]} />
        </div>
      )}
    </FixedSizeList>
  );
};
```

## 🧪 Testing

### Unit Tests (Vitest)
```typescript
// Component test example
describe('Button', () => {
  it('renders with correct variant', () => {
    render(<Button variant="primary">Click me</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-brand-500');
  });
  
  it('handles click events', async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    await userEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### E2E Tests (Playwright)
```typescript
// E2E test example
test('user can view dashboard', async ({ page }) => {
  await page.goto('/');
  await page.fill('[data-testid="email"]', 'user@example.com');
  await page.fill('[data-testid="password"]', 'password');
  await page.click('[data-testid="login-button"]');
  
  await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
  await expect(page.locator('[data-testid="metrics-card"]')).toHaveCount(4);
});
```

## 📦 Build Configuration

### Vite Config
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['chart.js', 'd3'],
          ui: ['@headlessui/react', 'framer-motion']
        }
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
});
```

## 🚀 Deployment

### Build Commands
```bash
# Development build
npm run build:dev

# Production build
npm run build

# Analyze bundle size
npm run build:analyze

# Preview production build
npm run preview
```

### Environment-Specific Configs
```typescript
// Config for different environments
const config = {
  development: {
    apiUrl: 'http://localhost:8000',
    wsUrl: 'ws://localhost:8000/ws',
    enableDebug: true
  },
  staging: {
    apiUrl: 'https://staging-api.reviewpulse.dev',
    wsUrl: 'wss://staging-api.reviewpulse.dev/ws',
    enableDebug: true
  },
  production: {
    apiUrl: 'https://api.reviewpulse.dev',
    wsUrl: 'wss://api.reviewpulse.dev/ws',
    enableDebug: false
  }
};
```

## 📚 Documentation

### Component Documentation
```typescript
/**
 * Button component for user interactions
 * 
 * @example
 * <Button variant="primary" size="md" onClick={handleClick}>
 *   Click me
 * </Button>
 */
interface ButtonProps {
  /** Button variant */
  variant?: 'primary' | 'secondary' | 'outline';
  /** Button size */
  size?: 'sm' | 'md' | 'lg';
  /** Click handler */
  onClick?: () => void;
  /** Button content */
  children: React.ReactNode;
}
```

### API Documentation
- Auto-generated with TypeDoc
- Interactive examples with Storybook
- Component playground

## 🔄 CI/CD Integration

### GitHub Actions
```yaml
# Frontend CI/CD
name: Frontend CI/CD
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run test
      - run: npm run test:e2e
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v3
        with:
          name: build
          path: dist/
```

## 🎯 Next Steps

1. **Set up development environment**
2. **Configure authentication provider**
3. **Connect to backend APIs**
4. **Implement core features**
5. **Add comprehensive testing**
6. **Deploy to staging**

The frontend is now ready for development with a modern, scalable architecture that provides an excellent user experience for the Review Pulse system.
