*** Settings ***
Library           SeleniumLibrary
Suite Setup       Open Browser To Login Page    

Test
    [Documentation]    This test verifies that the user can log in successfully with valid credentials.
    
    
    Log To Console    Starting the login test...
    