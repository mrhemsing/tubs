export const metadata = {
  title: 'Tubs Aerial Review',
  description: 'Aerial and elevated house plus backyard/lot candidate review.',
  icons: {
    icon: '/favicon.svg',
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
