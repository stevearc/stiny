angular.module('stiny')

# Parse out constants that were rendered to index.jinja2
.constant('CONST', angular.fromJson(angular.element(document.body).attr('constants')))

.config(['$httpProvider', ($httpProvider) ->
  $httpProvider.defaults.xsrfHeaderName = 'X-CSRF-Token'
  $httpProvider.defaults.xsrfCookieName = 'CSRF-Token'
])

.run(->
  FastClick.attach(document.body)
)

# Directive for focusing on an element
.directive('stFocus', ['$timeout', ($timeout) ->
  (scope, element, attrs) ->
    scope.$watch(attrs.stFocus,
      (newValue) ->
        if newValue
          $timeout(->
            element[0].focus()
            if not attrs.noScroll?
              window.scrollTo(0, element[0].offsetTop - 100)
          )
      , true)
])

# Intercept all HTTP errors. If they contain a nice code and message, log it to
# the console.
.config(['$httpProvider', ($httpProvider) ->
  $httpProvider.interceptors.push(['$q', '$injector', ($q, $injector) ->
    login = ['stAuth', (stAuth) ->
      stAuth.removeUser()
      stAuth.login()
    ]
    return {
      responseError: (response) ->
        if response.status == 401
          $injector.invoke(login)
        else if response.data.error? and response.data.msg?
          console.log("#{response.data.error}: #{response.data.msg}")
        $q.reject(response)
    }
  ])
])

# Object for handling login/credential/permissions methods
.factory('stAuth', ['$http', '$route', '$location', '$q',
($http, $route, $location, $q) -> {
    _user: null
    _permissions: []
    _loggingIn: false
    getUser: -> @_user
    setUser: (@_user) ->
    isLoggedIn: -> @_user?
    isLoggingIn: -> @_loggingIn
    setPermissions: (@_permissions) ->

    hasPermission: (perm) ->
      return true if not perm?
      if 'admin' in @_permissions
        return true
      if perm == 'login'
        return @isLoggedIn()
      return perm in @_permissions

    removeUser: ->
      @setUser null
      @setPermissions []

    logout: ->
      gapi.auth.signOut()
      @serverLogout()

    serverLogout: ->
      return unless @isLoggedIn()
      $http.post('/api/logout').success((data, status, headers, config) =>
        @removeUser()
        $route.reload()
      )

    serverLogin: (access_token) ->
      @_loggingIn = true
      deferred = $q.defer()
      $http.post('/api/login', {access_token: access_token})
      .success((data, status, headers, config) =>
        @setUser data.user
        @setPermissions data.permissions
        @_loggingIn = false
        deferred.resolve()
      ).error((data, status, headers, config) =>
        @_loggingIn = false
        deferred.reject()
      )
      return deferred.promise

    login: ->
      if @isLoggedIn()
        $location.url('/denied')
      else
        $location.url('/login')
  }
])

# On page load, set the user & permissions into stAuth
.run(['stAuth', 'CONST', (stAuth, CONST) ->
  if CONST.USER?
    stAuth.setUser(CONST.USER)
  if CONST.PERMISSIONS?
    stAuth.setPermissions(CONST.PERMISSIONS)
])

# Check permissions on every route change
.run(['$rootScope', 'stAuth', ($rootScope, stAuth) ->
  $rootScope.$on '$routeChangeStart', (event, newRoute, oldRoute) ->
    if not stAuth.hasPermission newRoute.permission
      stAuth.login()

  $rootScope.hasPerm = (perm) ->
    return stAuth.hasPermission perm
])
