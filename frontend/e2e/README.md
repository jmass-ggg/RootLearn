# End-to-End Tests with Playwright

This directory contains E2E tests for the RootLearn frontend application using Playwright.

## Overview

The E2E tests validate the complete user journey through the RootLearn application:

1. **Landing Page** - Session creation
2. **Graph Visualization** - Interactive prerequisite graph
3. **Diagnostic Assessment** - Question and answer flow
4. **Root Gap Detection** - Identification of knowledge gaps
5. **Socratic Tutoring** - Chat-based teaching interface
6. **Teach-Back Verification** - Student explanation evaluation

## Prerequisites

Before running E2E tests, ensure you have:

1. **Backend API running** on `http://localhost:8000`
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **PostgreSQL database** running and configured
   ```bash
   docker-compose up postgres
   ```

3. **Environment variables** configured for AI provider (OpenAI, Anthropic, or Google)
   ```bash
   export OPENAI_API_KEY=your_key_here
   # or
   export ANTHROPIC_API_KEY=your_key_here
   ```

4. **Playwright browsers** installed
   ```bash
   npx playwright install
   ```

## Running Tests

### Run all E2E tests
```bash
npm run test:e2e
```

This command will:
- Automatically start the Next.js dev server on `http://localhost:3000`
- Run all E2E tests in headless mode
- Generate an HTML report

### Run tests with UI mode (interactive)
```bash
npm run test:e2e:ui
```

This opens the Playwright UI where you can:
- See tests as they run
- Step through each test action
- Inspect DOM and network requests

### Run tests in debug mode
```bash
npm run test:e2e:debug
```

This runs tests with the Playwright Inspector for debugging.

### Run specific test file
```bash
npx playwright test learning-flow.spec.ts
```

### Run tests in headed mode (see browser)
```bash
npx playwright test --headed
```

## Test Structure

### `learning-flow.spec.ts`
Main test suite covering the complete happy path:

- **Complete Learning Flow** - Full journey from session creation to teach-back
- **Session Creation Errors** - Error handling validation
- **Graph Interactions** - Graph component testing

## Test Configuration

Configuration is in `playwright.config.ts`:

- **Browser**: Chromium (can be extended to Firefox, WebKit)
- **Base URL**: `http://localhost:3000`
- **Timeout**: 180 seconds for complete flow tests
- **Retries**: 0 locally, 2 on CI
- **Screenshots**: Captured on failure
- **Traces**: Captured on first retry

## Troubleshooting

### Tests timing out
- Ensure backend API is running and responding
- Check AI provider API key is valid and has credits
- Increase timeout in test configuration if needed

### "Cannot connect to localhost:3000"
- Ensure no other process is using port 3000
- Try running `npm run dev` manually first to verify the frontend starts

### Graph not rendering
- Check browser console for React Flow errors
- Ensure graph data is being returned from API
- Verify React Flow is properly installed

### AI responses taking too long
- AI calls can be slow, especially for complex prompts
- Consider using shorter prompts in tests
- Mock AI responses for faster test execution (advanced)

## Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Tests create sessions but don't clean up (consider adding cleanup)
3. **Waiting**: Use `waitForSessionStatus` helper for state transitions
4. **Assertions**: Use Playwright's built-in assertions with timeouts
5. **Debugging**: Use `page.pause()` to debug interactively

## CI/CD Integration

To run E2E tests in CI:

```yaml
- name: Install dependencies
  run: npm ci
  
- name: Install Playwright browsers
  run: npx playwright install --with-deps chromium
  
- name: Start backend
  run: |
    cd backend
    uvicorn app.main:app &
    
- name: Run E2E tests
  run: npm run test:e2e
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Future Improvements

- [ ] Add test for multiple diagnostic questions
- [ ] Test error states (API failures, network errors)
- [ ] Add test for session abandonment
- [ ] Mock AI responses for faster execution
- [ ] Add visual regression testing
- [ ] Test accessibility compliance
- [ ] Add performance metrics collection
