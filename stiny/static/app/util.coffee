angular.module('stiny')

.constant('CONST', angular.fromJson(angular.element(document.body).attr('constants')))

.config(['$httpProvider', ($httpProvider) ->
  $httpProvider.defaults.xsrfHeaderName = 'X-CSRF-Token'
  $httpProvider.defaults.xsrfCookieName = 'CSRF-Token'
])

.run(->
  FastClick.attach(document.body)
)

.config(['RestangularProvider', (RestangularProvider) ->
  RestangularProvider.setBaseUrl('/api')
])

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
