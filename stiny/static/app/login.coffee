angular.module('stiny')

.config(['$routeProvider', 'CONST', ($routeProvider, CONST) ->
  $routeProvider.when('/login', {
    controller: 'LoginCtrl'
    templateUrl: "#{ CONST.URL_PREFIX }/app/login.html"
  })
])

.config(['$routeProvider', 'CONST', ($routeProvider, CONST) ->
  $routeProvider.when('/denied', {
    templateUrl: "#{ CONST.URL_PREFIX }/app/denied.html"
  })
])

.controller('LoginCtrl',
['$scope', '$location', 'stAuth',
($scope, $location, stAuth) ->
  $scope.$watch ->
    stAuth.isLoggingIn()
  , (loggingIn) ->
    $scope.loggingIn = loggingIn

  $scope.$watch ->
    stAuth.isLoggedIn()
  , (loggedIn) ->
    if loggedIn
      $location.url('/')
])

.directive('stLoginLogout', ['$http', 'stAuth', 'CONST', ($http, stAuth, CONST) ->
  restrict: 'A'
  template: '<button ng-if="loginParams" st-google-login="loginParams"></button>'
  scope: {}
  link: (scope, element, attrs) ->
    loggingIn = false
    onLogin = (authResult) ->
      if authResult.error == 'user_signed_out'
        return
      if not authResult.status.signed_in
        console.error authResult.error
        return

      # Prevent duplicate login attempts
      return if stAuth.isLoggingIn()
      stAuth.serverLogin(authResult.access_token).catch ->
        alert("Login failed! #{ data.msg }")

    scope.loginParams =
      clientid: CONST.GOOGLE_CLIENT_ID
      cookiepolicy: 'single_host_origin'
      scope: 'email'
      callback: onLogin
])

# Directive to render the G+ login button
.directive('stGoogleLogin', ['CONST', (CONST) ->
  restrict: 'A'
  replace: true
  scope:
    parameters: '=stGoogleLogin'
  link: (scope, element, attrs) ->
    gapi.signin.render(element[0], scope.parameters)
])
