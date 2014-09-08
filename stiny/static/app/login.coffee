angular.module('stiny')

.config(['$routeProvider', 'CONST', ($routeProvider, CONST) ->
  $routeProvider.when('/login', {
    controller: 'LoginCtrl'
    templateUrl: "#{ CONST.URL_PREFIX }/app/login.html"
  })
])

.controller('LoginCtrl', ['$scope', '$http', '$location', 'stAuth', 'CONST',
($scope, $http, $location, stAuth, CONST) ->
  onLogin = (authResult) ->
    if authResult.error == 'user_signed_out'
      # FIXME: logout doesn't work yet
      # stAuth.serverLogout()
      return
    return unless authResult.status.signed_in

    $http.post('/api/login', {access_token: authResult.access_token}).success((data, status, headers, config) ->
      stAuth.setUser data.user
      stAuth.setPermissions data.permissions
      if $location.url() == '/login'
        $location.url('/')
    ).error((data, status, headers, config) ->
      alert("Login failed!")
    )

  $scope.loginParams = {
    clientid: CONST.GOOGLE_CLIENT_ID
    cookiepolicy: 'single_host_origin'
    scope: 'email'
    callback: onLogin
  }
])

.directive('stGoogleLogin', ['CONST', (CONST) ->
  restrict: 'A'
  replace: true
  scope:
    parameters: '=stGoogleLogin'
  link: (scope, element, attrs) ->
    gapi.signin.render(element[0], scope.parameters)

])
