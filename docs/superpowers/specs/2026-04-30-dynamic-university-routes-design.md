# Spec: Dynamic University Course Routes

Implementing a scalable way to view courses for a specific university while laying the groundwork for custom branding.

## Goal
Allow users to access university-specific course lists via clean URLs (e.g., `/courses/latrobe`) and eventually support unique branding per university.

## Architecture

### 1. Routing
- **Primary Route:** `web/src/app/courses/[slug]/page.tsx`
  - This dynamic route will capture the university slug from the URL.
- **Shortcuts (Optional):** We may implement redirects in `next.config.mjs` to map `/[slug]` to `/courses/[slug]` for top-level access if requested.

### 2. Data Flow
- **Input:** `slug` from route parameters.
- **DB Lookup:** 
  - Query `universities` table where `slug = params.slug`.
  - If not found, invoke `notFound()`.
- **Course Fetching:** 
  - Query `courses` table filtered by the found `university_id`.
  - Include joins for `course_campuses` and `campuses` to get ATARs and locations.
- **UI Interaction:** Pass the filtered courses and the specific university metadata to the `CourseListClient`.

### 3. Components
- **`CourseListClient` Updates:**
  - Support a "locked" or "initial" filter state for the university.
  - Display a university-specific banner if metadata is provided.
- **`FeaturedUniBanner`:** Enhance to handle data passed from the dynamic page.

### 4. Branding Hooks
The `[slug]/page.tsx` component will serve as a controller. In the future, it will be used to inject:
- Custom CSS variables (colors).
- University logos.
- Custom headers/footers.

## Success Criteria
1. Visiting `/courses/latrobe` displays only La Trobe University courses.
2. Visiting an invalid slug (e.g., `/courses/invalid-uni`) returns a 404 page.
3. The university filter in the UI reflects the current route context.
4. The implementation is generic and works for any university added to the database.

## Verification Plan
1. Manually navigate to `/courses/latrobe` and verify the list.
2. Verify that the "University" filter in the sidebar is correctly synchronized.
3. Attempt to visit a non-existent university slug and confirm the 404 behavior.
