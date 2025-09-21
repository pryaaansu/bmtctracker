# BMTC Transport Tracker

A comprehensive real-time public transport tracking system for BMTC Bengaluru, featuring live bus tracking, passenger notifications, driver management, and administrative oversight through a modern, highly interactive, and accessible interface.

## 🚀 Features

- **Real-time Bus Tracking**: Live GPS tracking with smooth animations
- **Bilingual Support**: English and Kannada interface
- **Multi-channel Notifications**: SMS, Voice, WhatsApp, and Push notifications
- **Interactive Maps**: Leaflet-based maps with clustering and smooth transitions
- **Responsive Design**: Mobile-first design with PWA capabilities
- **Admin Dashboard**: Comprehensive management interface
- **Driver Portal**: Mobile-friendly driver interface
- **Accessibility**: WCAG 2.1 AA compliant with TTS support

## 🛠 Technology Stack

### Frontend
- React 18 + TypeScript
- Vite for build tooling
- Tailwind CSS with custom design tokens
- Framer Motion for animations
- Leaflet for interactive maps
- React Query for data fetching
- i18next for internationalization

### Backend
- FastAPI (Python)
- SQLAlchemy ORM with MySQL
- Redis for caching and pub/sub
- WebSocket for real-time updates
- Celery for background tasks

### Infrastructure
- Docker & Docker Compose
- MySQL 8.0
- Redis 7

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bmtc-transport-tracker
   ```

2. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs

### Local Development

#### Frontend Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

#### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload
```

## 📱 Demo Accounts

- **Admin**: admin@bmtc.gov.in / admin123
- **Driver**: driver1@bmtc.gov.in / driver123
- **Test Phone**: +91-9876543210

## 🗂 Project Structure

```
bmtc-transport-tracker/
├── src/                    # Frontend React application
│   ├── components/         # Reusable UI components
│   ├── pages/             # Page components
│   ├── contexts/          # React contexts
│   ├── i18n/              # Internationalization
│   └── ...
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── core/          # Core configuration
│   └── ...
├── database/              # Database initialization
├── docker-compose.yml     # Docker services
└── README.md
```

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example`):

- `DATABASE_URL`: MySQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key
- `DEMO_MODE`: Enable/disable demo mode
- `TWILIO_*`: Twilio API credentials (for SMS/Voice)
- `EXOTEL_*`: Exotel API credentials

### Demo Mode

The application runs in demo mode by default, which:
- Uses mock data for bus locations
- Simulates notification delivery
- Provides sample routes and stops
- Enables all features without external dependencies

## 🚌 API Endpoints

### Core Endpoints
- `GET /api/v1/routes` - Get all routes
- `GET /api/v1/stops` - Get stops (with location filtering)
- `GET /api/v1/buses` - Get active buses
- `POST /api/v1/subscriptions` - Create notification subscription

### WebSocket
- `/ws/realtime` - Real-time bus location updates

### Documentation
- `/api/docs` - Interactive API documentation (Swagger)
- `/api/redoc` - Alternative API documentation

## 🌐 Internationalization

The application supports:
- **English** (default)
- **Kannada** (ಕನ್ನಡ)

Language files are located in `src/i18n/locales/`.

## 🎨 Design System

Custom Tailwind CSS configuration with:
- BMTC brand colors
- Responsive typography scale
- Animation utilities
- Dark mode support
- Accessibility-focused design tokens

## 📱 PWA Features

- Offline capability
- App-like experience
- Push notifications
- Service worker caching
- Installable on mobile devices

## 🧪 Testing

```bash
# Frontend tests
npm run test

# Backend tests
cd backend
pytest

# E2E tests
npm run test:e2e
```

## 🚀 Deployment

### Production Build

```bash
# Build frontend
npm run build

# Build and run with Docker
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Setup

1. Set `DEMO_MODE=false` for production
2. Configure real database and Redis instances
3. Set up SSL certificates
4. Configure notification service API keys

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the API documentation at `/api/docs`
- Review the project requirements and design documents

## 🎯 Roadmap

This is Task 1 of the implementation plan. Upcoming tasks include:
- Database models and repositories (Task 2)
- Mock data generator and location service (Task 3)
- Authentication system (Task 4)
- And many more features as outlined in the tasks.md file

---

**Built for BMTC Bengaluru** 🚌 **Made with ❤️ in India**# bmtctracker
