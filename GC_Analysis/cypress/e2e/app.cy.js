describe('Home page', () => {
  it('shows login form', () => {
    cy.visit('/');
    cy.contains('h2', 'Login').should('be.visible');
    cy.get('input[placeholder="Username"]').should('be.visible');
    cy.get('input[placeholder="Password"]').should('be.visible');
  });
});
